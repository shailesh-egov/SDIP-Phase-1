# encryptor.py
import os
import json
import base64
from typing import Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.utils.key_manager import KeyManager

class Encryptor:
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager

    def encrypt(self, data: Union[str, dict, list]) -> Union[str, dict]:
        if isinstance(data, (dict, list)):
            data_bytes = json.dumps(data).encode('utf-8')
            content_type = "json"
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
            content_type = "string"
        else:
            raise ValueError("Unsupported data type. Must be str, dict, or list.")

        key = self.key_manager.get_current_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data_bytes, None)
        key_id = self.key_manager.get_current_key_id()

        if content_type == "string":
            output_bytes = key_id.encode('utf-8') + nonce + ciphertext
            return base64.b64encode(output_bytes).decode('utf-8')
        else:
            payload = {
                "key_id": key_id,
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
                "content_type": content_type
            }
            return payload

    def decrypt(self, payload: Union[str, dict]) -> Union[str, dict, list]:
        if isinstance(payload, str):
            decoded = base64.b64decode(payload)
            key_id = decoded[:2].decode('utf-8')  # Assuming 2-char key_id (like 'v1')
            nonce = decoded[2:14]
            ciphertext = decoded[14:]

            key = self.key_manager.get_key(key_id)
            if not key:
                raise ValueError(f"Unknown key_id {key_id}")

            aesgcm = AESGCM(key)
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode('utf-8')

        elif isinstance(payload, dict):
            key_id = payload["key_id"]
            nonce = base64.b64decode(payload["nonce"])
            ciphertext = base64.b64decode(payload["ciphertext"])
            content_type = payload["content_type"]

            key = self.key_manager.get_key(key_id)
            if not key:
                raise ValueError(f"Unknown key_id {key_id}")

            aesgcm = AESGCM(key)
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)

            if content_type == "json":
                return json.loads(decrypted_bytes.decode('utf-8'))
            else:
                raise ValueError("Unsupported content_type in JSON payload.")

        else:
            raise ValueError("Unsupported payload type. Must be str or dict.")