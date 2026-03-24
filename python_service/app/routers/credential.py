"""凭证管理API路由（简化版）
Python 服务不再维护全局凭证，凭证完全由 Java 后端从 DB 读取后按请求传入。
此路由仅保留 status 接口供兼容查询。
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CredentialStatusResponse(BaseModel):
    has_credential: bool
    message: str


@router.get("/status", response_model=CredentialStatusResponse)
async def get_credential_status():
    """
    查询凭证状态。
    Python 服务不再维护全局凭证，凭证由 Java 后端按请求传入。
    """
    return CredentialStatusResponse(
        has_credential=False,
        message="凭证由 Java 后端管理，Python 服务按请求接收用户级凭证"
    )
