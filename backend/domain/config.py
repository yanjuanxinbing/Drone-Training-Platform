"""App-level configuration. Persisted to db/data/config.json."""
from __future__ import annotations

from .file import FileReader, FileWriter


class Config:
    def __init__(self):
        self.FILE = "config.json"
        self.CONFIG = {
            "agreed": False,        # 用户协议
            "language": "zh_CN",    # 语言
            "notify_enabled": True, # 提醒功能
            "last_user": "",        # 最后登录手机号
            "jwt_secret": "drone-training-platform-secret-key-change-in-production",
            "jwt_alg": "HS256",
            "jwt_expire_minutes": 60 * 24 * 7,
        }

        user_data = FileReader.read_json(self.FILE)
        # Backwards-compat: ignore unknown keys but never overwrite secrets if missing.
        for k, v in user_data.items():
            if k in self.CONFIG and k not in {"jwt_secret", "jwt_alg", "jwt_expire_minutes"}:
                self.CONFIG[k] = v
            elif k not in self.CONFIG:
                self.CONFIG[k] = v

    def get(self, key: str):
        return self.CONFIG.get(key)

    def set(self, key: str, value) -> None:
        self.CONFIG[key] = value
        self.save()

    def logout(self) -> None:
        self.CONFIG["last_user"] = ""
        self.save()

    def save(self) -> None:
        FileWriter.write_json(self.FILE, self.CONFIG)


# Singleton
config = Config()