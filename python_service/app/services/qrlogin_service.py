"""B站扫码登录服务"""
from typing import Dict
from bilibili_api import login_v2


class QRLoginService:
    """B站二维码登录服务"""

    def __init__(self):
        """初始化服务"""
        self.pending_logins = {}  # 存储待确认的登录会话 {qrcode_key: QrCodeLogin实例}

    async def generate_qrcode(self) -> Dict:
        """
        生成二维码

        Returns:
            {
                "qrcode_url": "二维码URL（前端用来生成二维码图片）",
                "qrcode_key": "二维码key（用于轮询状态）"
            }
        """
        # 创建QR登录实例 (使用WEB平台)
        qr_login = login_v2.QrCodeLogin(platform=login_v2.QrCodeLoginChannel.WEB)
        await qr_login.generate_qrcode()

        # 获取二维码信息
        qrcode_key = qr_login._QrCodeLogin__qr_key  # 访问私有属性
        qrcode_url = qr_login._QrCodeLogin__qr_link

        # 存储登录会话，后续轮询时使用
        self.pending_logins[qrcode_key] = qr_login

        return {
            "qrcode_url": qrcode_url,
            "qrcode_key": qrcode_key
        }

    async def check_qrcode_status(self, qrcode_key: str) -> Dict:
        """
        检查扫码状态

        Args:
            qrcode_key: 二维码key

        Returns:
            {
                "status": "pending|scanned|confirmed|expired",
                "message": "状态消息",
                "sessdata": "SESSDATA"（仅登录成功时）,
                "bili_jct": "bili_jct"（仅登录成功时）,
                "buvid3": "buvid3"（仅登录成功时）
            }
        """
        # 从会话中获取登录实例
        qr_login = self.pending_logins.get(qrcode_key)
        if not qr_login:
            return {
                "status": "error",
                "message": "二维码key不存在或已过期"
            }

        # 检查状态
        state = await qr_login.check_state()

        # 根据状态返回不同响应
        if state == login_v2.QrCodeLoginEvents.SCAN:
            return {
                "status": "pending",
                "message": "等待扫码"
            }
        elif state == login_v2.QrCodeLoginEvents.CONF:
            return {
                "status": "scanned",
                "message": "已扫码，请在手机上确认登录"
            }
        elif state == login_v2.QrCodeLoginEvents.TIMEOUT:
            # 清理过期会话
            del self.pending_logins[qrcode_key]
            return {
                "status": "expired",
                "message": "二维码已过期，请重新获取"
            }
        elif state == login_v2.QrCodeLoginEvents.DONE:
            # 登录成功，获取凭证
            credential = qr_login.get_credential()

            # 清理已完成的会话
            del self.pending_logins[qrcode_key]

            return {
                "status": "confirmed",
                "message": "登录成功",
                "sessdata": credential.sessdata,
                "bili_jct": credential.bili_jct,
                "buvid3": credential.buvid3
            }
        else:
            return {
                "status": "error",
                "message": f"未知状态: {state}"
            }
