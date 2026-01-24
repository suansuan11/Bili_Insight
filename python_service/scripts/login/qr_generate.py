# qr_generate.py
import requests
import json
import sys

def generate_qrcode_info():
    """
    请求B站API生成二维码，并返回 key 和 url
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, proxies={"http": None, "https": None})
        response.raise_for_status()
        data = response.json()

        if data.get("code") == 0:
            # 成功，将关键信息以JSON格式打印到标准输出
            result = {
                "status": "success",
                "qrcode_key": data["data"]["qrcode_key"],
                "url": data["data"]["url"]
            }
            print(json.dumps(result))
        else:
            raise Exception(f"API returned error: {data.get('message')}")

    except Exception as e:
        # 失败，打印错误信息到标准错误输出
        error_result = {"status": "error", "message": str(e)}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    generate_qrcode_info()