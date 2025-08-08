from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json

def generate_rsa_keys(username):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    # Ghi vào file
    filename = f"user_{username}_keys.json"
    with open(filename, 'w') as f:
        json.dump({
            "private_key": private_pem,
            "public_key": public_pem
        }, f)

    print(f" Đã tạo khóa cho user '{username}', lưu tại: {filename}")

# Tạo khóa cho nhiều user ở đây
usernames = ["admin", "duyen", "bao", "son", "linh"]  # <--- thêm tên user mới vào đây
for username in usernames:
    generate_rsa_keys(username)

