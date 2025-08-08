import hashlib
import time
from typing import Any

def generate_zkp(secret: Any) -> str:
    """
    Sinh Zero-Knowledge Proof (giả lập): hash của (secret + timestamp).
    """
    nonce = str(time.time())
    proof = hashlib.sha256((str(secret) + nonce).encode()).hexdigest()
    return proof

def verify_zkp(proof: str, secret: Any) -> bool:
    """
    Kiểm tra ZKP (giả lập): hash lại secret + timestamp lệch 1s.
    Trong thực tế cần ZKP thật, nhưng ở đây chỉ mô phỏng.
    """
    nonce = str(time.time() - 1)  # Cho phép lệch 1s
    expected_proof = hashlib.sha256((str(secret) + nonce).encode()).hexdigest()
    return proof == expected_proof
