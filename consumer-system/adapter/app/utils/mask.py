import hashlib

def mask_id_with_hash(original_id: str) -> str:
    return hashlib.sha256(original_id.encode()).hexdigest()
