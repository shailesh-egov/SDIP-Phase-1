# key_manager.py
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class KeyManager:
    def __init__(self, keys: dict, current_key_id: str):
        self.keys = keys
        self.current_key_id = current_key_id

    def get_key(self, key_id: str) -> bytes:
        return self.keys.get(key_id)

    def get_current_key(self) -> bytes:
        return self.keys[self.current_key_id]

    def get_current_key_id(self) -> str:
        return self.current_key_id