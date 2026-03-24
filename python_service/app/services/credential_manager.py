"""B站凭证管理器 - 完全依赖 Java 传入的用户级凭证，无全局默认凭证"""
from typing import Optional
from bilibili_api import Credential


def make_credential(sessdata: Optional[str],
                    bili_jct: Optional[str] = None,
                    buvid3: Optional[str] = None) -> Optional[Credential]:
    """
    根据 sessdata 创建 Credential 对象。

    Args:
        sessdata: 由 Java 后端从数据库读取后传入
        bili_jct: 可选
        buvid3:   可选

    Returns:
        Credential 对象；sessdata 为空时返回 None（游客模式）
    """
    if not sessdata:
        return None
    try:
        return Credential(sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)
    except Exception as e:
        print(f"[WARN] 创建 Credential 失败: {e}")
        return None


# ---------------------------------------------------------------------------
# 向后兼容：保留 get_credential_manager() 和 CredentialManager 供旧代码调用，
# 但内部不再维护任何全局凭证状态。
# ---------------------------------------------------------------------------

class CredentialManager:
    """轻量凭证管理器（无全局状态，仅作工厂）"""

    def get_credential(self, sessdata: Optional[str] = None,
                       bili_jct: Optional[str] = None,
                       buvid3: Optional[str] = None) -> Optional[Credential]:
        """根据传入的 sessdata 创建凭证；无 sessdata 则返回 None（游客模式）"""
        return make_credential(sessdata, bili_jct, buvid3)

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
