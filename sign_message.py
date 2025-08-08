# sign_message.py
import json
import sys
import time
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def sign_message_with_file(user_key_file, username):
    # Load private key
    with open(user_key_file, 'r') as f:
        keys = json.load(f)
        private_pem = keys['private_key']

    private_key = serialization.load_pem_private_key(
        private_pem.encode(),
        password=None,
    )

    # Tạo timestamp và thông điệp
    timestamp = int(time.time())
    message = f"{timestamp}:{username}"  # 🔥 phải đúng format giống backend
    payload = message.encode()

    # Ký thông điệp
    signature = private_key.sign(
        payload,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature).decode()

    print(f"Tạo chữ ký thành công!")
    print(f"Username : {username}")
    print(f"Timestamp: {timestamp}")
    print(f"Message  : {message}")
    print(f"Signature (base64): {signature_b64}")
    return timestamp, signature_b64

# Dùng như: python sign_message.py user_admin_keys.json admin
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python sign_message.py <user_key_file.json> <username>")
        sys.exit(1)

    key_file = sys.argv[1]
    username = sys.argv[2]
    sign_message_with_file(key_file, username)
