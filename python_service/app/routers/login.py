"""B站扫码登录API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.qrlogin_service import QRLoginService
from ..services.credential_manager import make_credential


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
    bili_jct: Optional[str] = None
    buvid3: Optional[str] = None
    cookie_json: Optional[str] = None


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
async def check_qr_status(qrcode_key: str):
    """
    检查扫码状态

    前端流程：
    1. 每隔2秒调用此接口检查状态
    2. status为"confirmed"时登录成功，Java 后端负责将 sessdata 持久化到 DB
    3. status为"expired"时需要重新获取二维码

    Args:
        qrcode_key: 二维码Key

    Returns:
        扫码状态（含 sessdata，由 Java 后端保存）
    """
    try:
        qr_service = get_qr_service()
        result = await qr_service.check_qrcode_status(qrcode_key)

        return QRStatusResponse(
            status=result["status"],
            message=result["message"],
            sessdata=result.get("sessdata"),
            bili_jct=result.get("bili_jct"),
            buvid3=result.get("buvid3"),
            cookie_json=result.get("cookie_json")
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"检查状态失败: {str(e)}"
        )


@router.get("/current_user")
async def get_current_user():
    """
    获取当前登录用户信息。
    注意：Python 服务不再维护全局凭证，此接口已由 Java 后端的
    /insight/login/current_user 替代（Java 从 DB 读取 sessdata 直接调用 B站 API）。
    """
    return {"is_login": False, "message": "请通过 Java 后端接口 /insight/login/current_user 获取用户信息"}
