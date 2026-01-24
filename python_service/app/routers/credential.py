"""凭证管理API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.credential_manager import get_credential_manager


router = APIRouter()


class CredentialRequest(BaseModel):
    """凭证请求模型"""
    sessdata: str
    bili_jct: Optional[str] = None
    buvid3: Optional[str] = None
    save_to_file: bool = True


class CredentialStatusResponse(BaseModel):
    """凭证状态响应"""
    has_credential: bool
    message: str


@router.post("/update")
async def update_credential(request: CredentialRequest):
    """
    更新系统凭证

    Java后端可以调用此接口更新Python服务的凭证
    这样就不需要手动复制粘贴了

    Args:
        request: 凭证信息

    Returns:
        更新结果
    """
    try:
        cred_manager = get_credential_manager()

        success = cred_manager.update_credential(
            sessdata=request.sessdata,
            bili_jct=request.bili_jct,
            buvid3=request.buvid3,
            save_to_file=request.save_to_file
        )

        if success:
            return {
                "status": "success",
                "message": "凭证更新成功，系统现在可以获取完整数据"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="凭证更新失败，请检查凭证格式"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新凭证时发生错误: {str(e)}"
        )


@router.get("/status", response_model=CredentialStatusResponse)
async def get_credential_status():
    """
    查询凭证状态

    Returns:
        凭证状态信息
    """
    cred_manager = get_credential_manager()
    has_credential = cred_manager.has_credential()

    return CredentialStatusResponse(
        has_credential=has_credential,
        message="系统已配置凭证，可获取完整数据" if has_credential else "系统未配置凭证，部分功能受限"
    )


@router.delete("/clear")
async def clear_credential():
    """
    清除系统凭证

    Returns:
        清除结果
    """
    try:
        # 创建一个空凭证（相当于清除）
        cred_manager = get_credential_manager()
        cred_manager._default_credential = None

        return {
            "status": "success",
            "message": "凭证已清除，系统将使用游客模式"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清除凭证时发生错误: {str(e)}"
        )
