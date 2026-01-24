# test_qr_login.py
import requests
import json
import time
import qrcode # 导入我们刚刚安装的库

def generate_qrcode_info():
    """
    步骤一：请求B站API生成二维码信息
    """
    print("正在向B站请求二维码...")
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, proxies={"http": None, "https": None})
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            print("二维码请求成功！")
            return data["data"]
        else:
            print(f"API返回错误: {data.get('message')}")
            return None
    except Exception as e:
        print(f"请求二维码时发生网络错误: {e}")
        return None

def poll_qrcode_status(qrcode_key):
    """
    步骤三：根据 qrcode_key 轮询扫码状态
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    params = {"qrcode_key": qrcode_key}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, params=params, headers=headers, proxies={"http": None, "https": None})
        response.raise_for_status()
        data = response.json()
        
        # 登录成功，响应中会包含 Set-Cookie 头
        if data.get("data", {}).get("code") == 0:
            cookies = response.cookies.get_dict()
            data["data"]["cookies"] = cookies
            
        return data["data"]
    except Exception as e:
        print(f"轮询状态时发生网络错误: {e}")
        return None

def main_test_flow():
    """
    主测试流程函数
    """
    # 1. 生成二维码
    qr_info = generate_qrcode_info()
    if not qr_info:
        return

    qrcode_key = qr_info["qrcode_key"]
    login_url = qr_info["url"]

    # 2. 在终端显示二维码
    qr = qrcode.QRCode()
    qr.add_data(login_url)
    print("\n请使用B站手机客户端扫描下方二维码：")
    qr.print_tty() # 在终端打印二维码

    # 3. 开始轮询状态
    try:
        while True:
            poll_result = poll_qrcode_status(qrcode_key)
            if not poll_result:
                break
            
            code = poll_result.get("code")
            message = poll_result.get("message")

            if code == 0:
                print("\n\n✅ 登录成功！")
                cookies = poll_result.get("cookies", {})
                print("获取到的Cookies信息如下:")
                # 为了美观，使用json格式化打印
                print(json.dumps(cookies, indent=4))
                break
            elif code == 86101: # 86101: 未扫码
                print("⏳ 状态: 等待扫描中...")
            elif code == 86090: # 86090: 已扫码，待确认
                print("⏳ 状态: 已扫描，请在手机上点击确认登录...")
            elif code == 86038: # 86038: 二维码已失效
                print("\n\n❌ 登录失败: 二维码已过期。")
                break
            else:
                print(f"\n\n❌ 登录失败: {message} (code: {code})")
                break
            
            time.sleep(2) # 每2秒查询一次状态

    except KeyboardInterrupt:
        print("\n用户手动中断了测试。")
    
    print("\n测试流程结束。")

if __name__ == "__main__":
    main_test_flow()