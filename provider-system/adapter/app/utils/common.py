import json
from app.utils.encryptor import Encryptor
from app.utils.key_manager import KeyManager
from app.core.config import ENCRYPTION_KEYS, CURRENT_KEY_ID

def encrypt_and_save_to_file(data, file_path):
    """
    Encrypts the given data and saves it to the specified file.
    """
    key_manager = KeyManager(ENCRYPTION_KEYS, CURRENT_KEY_ID)
    encryptor = Encryptor(key_manager)

    encrypted_data = encryptor.encrypt(data)

    with open(file_path, "w") as file:
        json.dump(encrypted_data, file, indent=2)