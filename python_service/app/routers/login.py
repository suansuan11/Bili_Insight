"""B站扫码登录API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.qrlogin_service import QRLoginService
from ..services.credential_manager import get_credential_manager


router = APIRouter()

# 全局服务实例
_qr_service_instance = None


def get_qr_service() -> QRLoginService:
    """获取QR登录服务单例"""
    global _qr_service_instance
    if _qr_service_instance is None:
        _qr_service_instance = QRLoginService()
    return _qr_service_instance


class QRCodeResponse(BaseModel):
    """二维码响应"""
    qrcode_url: str
    qrcode_key: str


class QRStatusResponse(BaseModel):
    """扫码状态响应"""
    status: str
    message: str
    sessdata: Optional[str] = None


@router.get("/qrcode", response_model=QRCodeResponse)
async def get_qrcode():
    """
    获取登录二维码

    前端流程：
    1. 调用此接口获取qrcode_url和qrcode_key
    2. 使用qrcode_url生成二维码图片显示给用户
    3. 使用qrcode_key轮询 /login/status

    Returns:
        二维码URL和Key
    """
    try:
        qr_service = get_qr_service()
        qr_data = await qr_service.generate_qrcode()
        return QRCodeResponse(
            qrcode_url=qr_data["qrcode_url"],
            qrcode_key=qr_data["qrcode_key"]
        )
    except Exception as e:
        import traceback
        print(f"QR Code generation error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"生成二维码失败: {str(e)}"
        )


@router.get("/status/{qrcode_key}", response_model=QRStatusResponse)
async def check_qr_status(qrcode_key: str, auto_save: bool = True):
    """
    检查扫码状态

    前端流程：
    1. 每隔2秒调用此接口检查状态
    2. status为"confirmed"时登录成功，可以保存sessdata
    3. status为"expired"时需要重新获取二维码

    Args:
        qrcode_key: 二维码Key
        auto_save: 是否自动保存凭证到系统（默认true）

    Returns:
        扫码状态
    """
    try:
        qr_service = get_qr_service()
        result = await qr_service.check_qrcode_status(qrcode_key)

        # 登录成功且需要自动保存
        if result["status"] == "confirmed" and auto_save:
            cred_manager = get_credential_manager()
            cred_manager.update_credential(
                sessdata=result["sessdata"],
                bili_jct=result.get("bili_jct"),
                buvid3=result.get("buvid3"),
                save_to_file=True
            )

        return QRStatusResponse(
            status=result["status"],
            message=result["message"],
            sessdata=result.get("sessdata")
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"检查状态失败: {str(e)}"
        )


@router.get("/current_user")
async def get_current_user():
    """
    获取当前登录用户信息
    
    Returns:
        用户信息或401未登录
    """
    try:
        cred_manager = get_credential_manager()
        credential = cred_manager.get_credential()
        
        if not credential:
            raise HTTPException(status_code=401, detail="未登录")
            
        # 使用凭证获取用户信息
        from bilibili_api import user
        try:
            # 获取自己的信息需要用 Credential 实例
            # 这里简单通过 REST API 验证或者让前端展示已登录状态
            # 为了获取头像昵称，我们需要调用 B站 API
            # 使用 bilibili_api 的 user.get_self_info (需要Credential)
            
            # 临时构造 Credential 对象
            from bilibili_api import Credential
            creds = Credential(
                sessdata=credential.sessdata, 
                bili_jct=credential.bili_jct, 
                buvid3=credential.buvid3
            )
            
            # 使用 get_self_info() 实际上是获取当前登录者的导航信息
            # 但 bilibili_api 的 user 模块主要针对特定 UID
            # 我们可以用 verify() 来检查有效性并获取信息
            if await creds.check_valid():
                # 获取导航栏信息 (包含头像昵称)
                from bilibili_api import client
                # 直接调用 API: https://api.bilibili.com/x/web-interface/nav
                resp = await client.request("GET", "https://api.bilibili.com/x/web-interface/nav", credential=creds)
                data = resp.get("data", {})
                
                return {
                    "is_login": True,
                    "uname": data.get("uname"),
                    "face": data.get("face"),
                    "level_info": data.get("level_info", {}),
                    "vip_label": data.get("vip_label", {}),
                    "wbi_img": data.get("wbi_img", {}) 
                }
            else:
                return {"is_login": False}
                
        except Exception as api_err:
            print(f"Bilibili API Error: {api_err}")
            # sessdata可能过期
            return {"is_login": False}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Check login error: {e}")
        return {"is_login": False}
