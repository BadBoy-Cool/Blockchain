from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import json

class CryptoUtils:
    def __init__(self):
        # Tạo khóa cố định hoặc đọc từ file
        self.key_file = 'crypto_keys.json'
        self.load_or_create_keys()

    def load_or_create_keys(self):
        """Tải khóa từ file hoặc tạo mới nếu chưa có"""
        try:
            with open(self.key_file, 'r') as f:
                keys_data = json.load(f)
                self.key = bytes.fromhex(keys_data['aes_key'])
                self.iv = bytes.fromhex(keys_data['iv'])
                # Tải RSA private key
                from cryptography.hazmat.primitives.serialization import load_pem_private_key
                self.rsa_key = load_pem_private_key(
                    keys_data['rsa_private_key'].encode(),
                    password=None,
                    backend=default_backend()
                )
        except (FileNotFoundError, KeyError, json.JSONDecodeError):
            # Tạo khóa mới nếu file không tồn tại
            self.key = os.urandom(32)  # Khóa AES 256-bit
            self.iv = os.urandom(16)   # Vector khởi tạo cho AES
            self.rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            self.save_keys()

    def save_keys(self):
        """Lưu khóa vào file"""
        keys_data = {
            'aes_key': self.key.hex(),
            'iv': self.iv.hex(),
            'rsa_private_key': self.rsa_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
        }
        with open(self.key_file, 'w') as f:
            json.dump(keys_data, f)

    def aes_encrypt(self, data):
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padded_data = data + " " * (16 - len(data) % 16)  # Padding
        return encryptor.update(padded_data.encode()) + encryptor.finalize()

    def aes_decrypt(self, encrypted_data):
        """Giải mã dữ liệu AES"""
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
        # Loại bỏ padding (khoảng trắng ở cuối)
        return decrypted_padded.decode().rstrip()

    def sign_transaction(self, transaction):
        return self.rsa_key.sign(
            json.dumps(transaction, sort_keys=True).encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

    def get_public_key(self):
        return self.rsa_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()