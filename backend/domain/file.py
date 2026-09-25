"""Filesystem utilities. Resolves the project `db/` directory automatically.

The project root is found by walking up from this file until a directory
containing `db/` is encountered. This keeps the data location stable
regardless of where the FastAPI process is launched from.
"""
from __future__ import annotations

import os
import json


def _resolve_root() -> str:
    """Find the project root that contains the `db/` directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        candidate = os.path.join(here, "db")
        if os.path.isdir(candidate):
            return os.path.dirname(candidate) if os.path.basename(here) == "domain" else here
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    # Fallback: assume `db/` is a sibling of the working directory.
    return os.getcwd()


ROOT = _resolve_root()


class FileReader:
    @staticmethod
    def read_txt(filename: str, subdir: str = "txt") -> str:
        path = f"{ROOT}/db/{subdir}/{filename}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"FileReader: 文件不存在 - {path}")
            return ""
        except Exception as e:
            print(f"FileReader: 读取失败 - {path} ({e})")
            return ""

    @staticmethod
    def read_json(filename: str, subdir: str = "data") -> dict:
        path = f"{ROOT}/db/{subdir}/{filename}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"FileReader: JSON 文件不存在 - {path}")
            return {}
        except Exception as e:
            print(f"FileReader: JSON 解析失败 - {path} ({e})")
            return {}

    @staticmethod
    def read_img(filename: str, subdir: str = "img") -> bytes | None:
        path = f"{ROOT}/db/{subdir}/{filename}"
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception as e:
                print(f"读取图片出错: {e}")
                return None
        return None


class FileWriter:
    @staticmethod
    def write_json(filename: str, content, subdir: str = "data"):
        path = f"{ROOT}/db/{subdir}/{filename}"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"FileWriter: JSON 写入失败 - {path} ({e})")

    @staticmethod
    def save_avatar(filename: str, content: bytes, subdir: str = "img") -> str:
        path = f"{ROOT}/db/{subdir}/{filename}"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, "wb") as f:
                f.write(content)
        except Exception as e:
            print(f"FileWriter: AVATAR 保存失败 - {path} ({e}")