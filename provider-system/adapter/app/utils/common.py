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

def decrypt_file(file_path):
    """
    Decrypts the contents of the given encrypted file and returns the original data.
    Logs key selection based on file's embedded key_id.
    """
    import logging
    logger = logging.getLogger(__name__)

    with open(file_path, "r") as file:
        encrypted_data = json.load(file)

    key_id = encrypted_data.get("key_id")
    logger.debug(f"Decrypting file: {file_path}, using key_id: {key_id}")

    key_manager = KeyManager(ENCRYPTION_KEYS, CURRENT_KEY_ID)
    encryptor = Encryptor(key_manager)

    return encryptor.decrypt(encrypted_data)