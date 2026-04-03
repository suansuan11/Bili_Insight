"""B站凭证管理器 - 仅使用 Java 传入的用户级凭证，无则游客模式"""
import json
from typing import Optional
from bilibili_api import Credential

from ..utils.logger import logger


def make_credential(sessdata: Optional[str],
                    bili_jct: Optional[str] = None,
                    buvid3: Optional[str] = None,
                    cookie_json: Optional[str] = None) -> Optional[Credential]:
    """
    根据 sessdata 创建 Credential 对象。

    仅使用 Java 后端显式传入的用户级凭证；若为空则进入游客模式。

    Args:
        sessdata: 由 Java 后端从数据库读取后传入
        bili_jct: 可选
        buvid3:   可选

    Returns:
        Credential 对象；所有来源均为空时返回 None（游客模式）
    """
    effective_sessdata = (sessdata or "").strip() or None

    if cookie_json:
        try:
            parsed = json.loads(cookie_json)
            if isinstance(parsed, dict):
                if effective_sessdata:
                    parsed.setdefault("SESSDATA", effective_sessdata)
                if bili_jct:
                    parsed.setdefault("bili_jct", bili_jct)
                if buvid3:
                    parsed.setdefault("buvid3", buvid3)
                credential = Credential.from_cookies(parsed)
                if credential.has_sessdata():
                    return credential
        except Exception as e:
            logger.warning(f"从 cookie_json 创建 Credential 失败，将退回简化凭证: {e}")

    if not effective_sessdata:
        logger.warning("无可用 SESSDATA，将以游客模式访问B站API（评论数量可能受限）")
        return None

    try:
        return Credential(sessdata=effective_sessdata, bili_jct=bili_jct, buvid3=buvid3)
    except Exception as e:
        logger.warning(f"创建 Credential 失败: {e}")
        return None


# ---------------------------------------------------------------------------
# 向后兼容：保留 get_credential_manager() 和 CredentialManager 供旧代码调用，
# 但内部不再维护任何全局凭证状态。
# ---------------------------------------------------------------------------

class CredentialManager:
    """轻量凭证管理器（无全局状态，仅作工厂）"""

    def get_credential(self, sessdata: Optional[str] = None,
                       bili_jct: Optional[str] = None,
                       buvid3: Optional[str] = None,
                       cookie_json: Optional[str] = None) -> Optional[Credential]:
        """根据传入的 sessdata 创建凭证；无 sessdata 则返回 None（游客模式）"""
        return make_credential(sessdata, bili_jct, buvid3, cookie_json)

    def has_credential(self) -> bool:
        """始终返回 False，全局凭证已移除"""
        return False


_credential_manager: Optional[CredentialManager] = None


def get_credential_manager() -> CredentialManager:
    """获取全局凭证管理器实例（向后兼容）"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager
