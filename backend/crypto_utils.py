import json
import base64
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.algorithms import AES

class CryptoUtils:
    def __init__(self):
        self.key_file = 'crypto_keys.json'
        self.load_or_create_keys()

    def load_or_create_keys(self):
        try:
            with open(self.key_file, 'r') as f:
                keys = json.load(f)
                self.key = bytes.fromhex(keys['aes_key'])           # 🔧 Bổ sung
                self.iv = bytes.fromhex(keys['iv'])                 # 🔧 Bổ sung
                self.rsa_private_key = serialization.load_pem_private_key(
                    keys['rsa_private_key'].encode(),
                    password=None,
                    backend=default_backend()
                )
        except Exception:
            # Tạo mới nếu chưa tồn tại
            self.key = os.urandom(32)  # 🔐 AES-256
            self.iv = os.urandom(16)   # 📦 AES block size
            self.rsa_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            self.save_keys()


    def save_keys(self):
        data = {
            'aes_key': self.key.hex(),
            'iv': self.iv.hex(),
            'rsa_private_key': self.rsa_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
        }
        with open(self.key_file, 'w') as f:
            json.dump(data, f)

    def pkcs7_pad(self, data: bytes) -> bytes:
        """Thêm padding để data dài đúng block size (AES = 16 bytes)"""
        block_size = algorithms.AES.block_size  
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def sign_login_message(self, username, timestamp=None):
        if timestamp is None:
            from time import time
            timestamp = int(time())

        message = f"{timestamp}:{username}".encode()
        signature = self.rsa_private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return timestamp, base64.b64encode(signature).decode()

    def get_public_key(self):
        return self.rsa_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def aes_decrypt(self, encrypted_data):
        """Giải mã dữ liệu AES với PKCS7 padding"""
        try:
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            decryptor = cipher.decryptor()

            # Giải mã
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()

            # Loại bỏ padding
            decrypted_data = self.pkcs7_unpad(decrypted_padded)

            # Trả về string
            return decrypted_data.decode('utf-8')

        except Exception as e:
            print(f"Error decrypting data: {e}")
            raise Exception("❌ Giải mã thất bại: " + str(e))
        
    def aes_encrypt(self, data):
        """Mã hóa AES với PKCS7 padding chuẩn"""
        try:
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # Chuyển string thành bytes nếu cần
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data

            # Áp dụng PKCS7 padding
            padded_data = self.pkcs7_pad(data_bytes)

            # Mã hóa
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            return encrypted

        except Exception as e:
            print(f"Error encrypting data: {e}")
            raise Exception("❌ Mã hóa thất bại: " + str(e))


    def pkcs7_unpad(self, data):
        padding_length = data[-1]
        return data[:-padding_length]

    @staticmethod
    def generate_rsa_key_pair(save_to=None):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        if save_to:
            with open(save_to, "w") as f:
                json.dump({
                    "private_key": private_pem,
                    "public_key": public_pem
                }, f)

        return {
            "private_key": private_pem,
            "public_key": public_pem
        }


def verify_signature(public_key_pem, message, signature_b64):
    try:
        public_key = serialization.load_pem_public_key(public_key_pem.encode())

        public_key.verify(
            base64.b64decode(signature_b64),
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        print("⛔ Signature verify failed:", e)
        return False



