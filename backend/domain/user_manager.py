"""User management.

Password hashing uses bcrypt for new accounts. Existing SHA-256 hashes (from
the legacy Flet app) are auto-upgraded to bcrypt on a successful login.
"""
from __future__ import annotations

import hashlib
from typing import Optional

from passlib.context import CryptContext

from .file import FileReader, FileWriter


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserManager:
    FILE = "users.json"

    def __init__(self):
        self.users = FileReader.read_json(self.FILE)

    # ── Hashing ────────────────────────────────────────────────────────────
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash with bcrypt."""
        return _pwd_context.hash(password)

    @staticmethod
    def _is_legacy_sha256(value: str) -> bool:
        """A bcrypt hash always starts with `$2b$`/`$2a$`. A plain SHA-256
        hex digest is exactly 64 lowercase hex chars."""
        if not value or not isinstance(value, str):
            return False
        if value.startswith("$2"):
            return False
        return len(value) == 64 and all(c in "0123456789abcdef" for c in value)

    def _verify(self, stored: str, plain: str) -> bool:
        if self._is_legacy_sha256(stored):
            legacy = hashlib.sha256(plain.encode("utf-8")).hexdigest()
            return legacy == stored
        try:
            return _pwd_context.verify(plain, stored)
        except Exception:
            return False

    # ── User CRUD ──────────────────────────────────────────────────────────
    def get(self, phone: str) -> Optional[dict]:
        return self.users.get(phone)

    def contains(self, phone: str) -> bool:
        return phone in self.users

    def add(self, phone: str, nick_name: str, password: str) -> None:
        self.users[phone] = {
            "nick_name": nick_name,
            "password": self._hash_password(password),
            "gender": "保密",
            "birthday": "",
            "addresses": [],
            "orders": [],
            "is_real_name_verified": False,
            "is_pilot_verified": False,
        }
        self.save()

    def delete(self, phone: str) -> None:
        self.users.pop(phone, None)
        self.save()

    def verify_login(self, phone: str, input_password: str) -> bool:
        user = self.users.get(phone)
        if not user:
            return False
        if self._verify(user["password"], input_password):
            # Upgrade legacy SHA-256 on success.
            if self._is_legacy_sha256(user["password"]):
                user["password"] = self._hash_password(input_password)
                self.save()
            return True
        return False

    def update_value(self, phone, nick_name, gender, birthday) -> None:
        self.users[phone]["nick_name"] = nick_name
        self.users[phone]["gender"] = gender
        self.users[phone]["birthday"] = birthday
        self.save()

    def update_password(self, phone, new_password: str) -> None:
        self.users[phone]["password"] = self._hash_password(new_password)
        self.save()

    def update_key(self, phone_old: str, phone_new: str) -> bool:
        if self.contains(phone_new):
            return False
        user = self.get(phone_old).copy()
        self.users.pop(phone_old)
        self.users[phone_new] = user
        self.save()
        return True

    # ── Addresses ──────────────────────────────────────────────────────────
    def realname(self, phone: str) -> bool:
        u = self.get(phone)
        return bool(u and u.get("is_real_name_verified"))

    def pilot(self, phone: str) -> bool:
        u = self.get(phone)
        return bool(u and u.get("is_pilot_verified"))

    def get_addresses(self, phone: str) -> list:
        u = self.get(phone)
        return list(u.get("addresses", [])) if u else []

    def get_location_by_address(self, phone: str, address: str) -> Optional[str]:
        for a in self.get_addresses(phone):
            if a["address"] == address:
                return a["location"]
        return None

    def add_address(self, phone: str, address: str, location: str) -> None:
        addresses = self.get_addresses(phone)
        new_id = str(int(addresses[-1]["id"]) + 1) if addresses else "1"
        addresses.append({"id": new_id, "address": address, "location": location})
        self.save()

    def update_address(self, phone: str, addr_id: str, address: str, location: str) -> None:
        for addr in self.get_addresses(phone):
            if addr["id"] == addr_id:
                addr["address"] = address
                addr["location"] = location
                self.save()
                return

    def set_default_address(self, phone: str, addr_id: str) -> None:
        addresses = self.get_addresses(phone)
        idx = next((i for i, a in enumerate(addresses) if a["id"] == addr_id), None)
        if idx is None or idx == 0:
            return
        addresses[0], addresses[idx] = addresses[idx], addresses[0]
        self.save()

    def delete_address(self, phone: str, addr_id: str) -> None:
        self.users[phone]["addresses"] = [
            a for a in self.get_addresses(phone) if a["id"] != addr_id
        ]
        self.save()

    # ── Orders ─────────────────────────────────────────────────────────────
    def get_orders(self, phone: str) -> list:
        u = self.get(phone)
        return list(u.get("orders", [])) if u else []

    def add_order(self, phone: str, order: dict) -> None:
        self.users[phone]["orders"].append(order)
        self.save()

    def get_order_by_id(self, phone: str, order_id: str) -> Optional[dict]:
        for order in self.get_orders(phone):
            if order.get("id") == order_id:
                return order
        return None

    def update_order_status(self, phone: str, order_id: str, status: str) -> None:
        for order in self.get_orders(phone):
            if order.get("id") == order_id:
                order["status"] = status
                self.save()
                return

    def cancel_order(self, phone: str, order_id: str) -> None:
        self.update_order_status(phone, order_id, "已取消")

    # ── Persistence ────────────────────────────────────────────────────────
    def save(self) -> None:
        FileWriter.write_json(self.FILE, self.users)


# Singleton
user_manager = UserManager()