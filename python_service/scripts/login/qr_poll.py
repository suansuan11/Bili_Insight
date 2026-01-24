# qr_poll.py
import requests
import json
import argparse
import sys

def poll_qrcode_status(qrcode_key):
    """
    根据 qrcode_key 轮询扫码状态
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    params = {"qrcode_key": qrcode_key}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, params=params, headers=headers, proxies={"http": None, "https": None})
        response.raise_for_status()
        data = response.json().get("data", {})
        
        result = {"code": data.get("code"), "message": data.get("message")}

        # code 为 0 表示登录成功
        if data.get("code") == 0:
            cookies = response.cookies.get_dict()
            sessdata = cookies.get("SESSDATA")
            bili_jct = cookies.get("bili_jct")
            
            if sessdata:
                result["status"] = "success"
                result["cookies"] = {
                    "SESSDATA": sessdata,
                    "bili_jct": bili_jct
                    # 可以按需添加其他cookie
                }
            else:
                result["status"] = "error"
                result["message"] = "Login succeeded but SESSDATA not found in cookies."
        
        print(json.dumps(result))

    except Exception as e:
        error_result = {"status": "error", "message": str(e)}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poll Bilibili QR code login status.")
    parser.add_argument("--key", required=True, help="The qrcode_key from generate API.")
    args = parser.parse_args()
    poll_qrcode_status(args.key)