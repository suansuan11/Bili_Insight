"""B站凭证管理器 - 统一管理和分发凭证"""
import json
import os
from pathlib import Path
from typing import Optional
from bilibili_api import Credential


class CredentialManager:
    """B站凭证管理器"""

    def __init__(self):
        """初始化凭证管理器"""
        self._default_credential: Optional[Credential] = None
        self._load_default_credential()

    def _load_default_credential(self):
        """
        从多个来源加载默认凭证

        优先级：
        1. credentials.json 文件
        2. 环境变量
        3. config.py配置
        """
        # 方式1: 从credentials.json读取
        credential = self._load_from_file()
        if credential:
            self._default_credential = credential
            print("[OK] 凭证管理器：从 credentials.json 加载默认凭证")
            return

        # 方式2: 从环境变量读取
        credential = self._load_from_env()
        if credential:
            self._default_credential = credential
            print("[OK] 凭证管理器：从环境变量加载默认凭证")
            return

        # 无凭证
        print("[WARN] 凭证管理器：未找到默认凭证，将使用游客模式")

    def _load_from_file(self) -> Optional[Credential]:
        """从credentials.json加载"""
        cred_file = Path(__file__).parent.parent.parent / "credentials.json"
        if not cred_file.exists():
            return None

        try:
            with open(cred_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sessdata = data.get('sessdata', '')

                if sessdata and sessdata not in ['', 'your_sessdata_here']:
                    return Credential(
                        sessdata=sessdata,
                        bili_jct=data.get('bili_jct') or None,
                        buvid3=data.get('buvid3') or None
                    )
        except Exception as e:
            print(f"[WARN] 读取 credentials.json 失败: {e}")

        return None

    def _load_from_env(self) -> Optional[Credential]:
        """从环境变量加载"""
        sessdata = os.getenv('BILI_SESSDATA')
        if sessdata:
            return Credential(
                sessdata=sessdata,
                bili_jct=os.getenv('BILI_JCT'),
                buvid3=os.getenv('BILI_BUVID3')
            )
        return None

    def get_credential(self, sessdata: Optional[str] = None) -> Optional[Credential]:
        """
        获取凭证

        Args:
            sessdata: 如果提供，创建临时凭证；否则返回默认凭证

        Returns:
            Credential对象或None
        """
        # 如果提供了sessdata，创建临时凭证（Java后端传递的场景）
        if sessdata:
            try:
                return Credential(sessdata=sessdata)
            except Exception as e:
                print(f"创建临时凭证失败: {e}")
                return None

        # 返回默认凭证
        return self._default_credential

    def has_credential(self) -> bool:
        """检查是否有默认凭证"""
        return self._default_credential is not None

    def update_credential(self, sessdata: str, bili_jct: Optional[str] = None,
                         buvid3: Optional[str] = None, save_to_file: bool = True):
        """
        更新凭证

        Args:
            sessdata: SESSDATA
            bili_jct: bili_jct（可选）
            buvid3: buvid3（可选）
            save_to_file: 是否保存到文件（默认True）
        """
        try:
            # 创建新凭证
            new_credential = Credential(
                sessdata=sessdata,
                bili_jct=bili_jct,
                buvid3=buvid3
            )

            # 更新默认凭证
            self._default_credential = new_credential

            # 保存到文件
            if save_to_file:
                self._save_to_file(sessdata, bili_jct, buvid3)

            print("[OK] 凭证更新成功")
            return True

        except Exception as e:
            print(f"[ERROR] 凭证更新失败: {e}")
            return False

    def _save_to_file(self, sessdata: str, bili_jct: Optional[str], buvid3: Optional[str]):
        """保存凭证到文件"""
        cred_file = Path(__file__).parent.parent.parent / "credentials.json"

        data = {
            "comment": "B站登录凭证配置 - 由系统自动更新",
            "sessdata": sessdata,
            "bili_jct": bili_jct or "",
            "buvid3": buvid3 or "",
            "note": "由凭证管理器自动保存"
        }

        with open(cred_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# 全局单例
_credential_manager = None


def get_credential_manager() -> CredentialManager:
    """获取全局凭证管理器实例"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager()
    return _credential_manager
