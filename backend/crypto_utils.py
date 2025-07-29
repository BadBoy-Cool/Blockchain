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

    def _pkcs7_pad(self, data):
        """PKCS7 padding chuẩn cho AES"""
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding

    def _pkcs7_unpad(self, data):
        """Loại bỏ PKCS7 padding"""
        padding_length = data[-1]
        return data[:-padding_length]

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
            padded_data = self._pkcs7_pad(data_bytes)
            
            # Mã hóa
            encrypted = encryptor.update(padded_data) + encryptor.finalize()
            return encrypted
            
        except Exception as e:
            print(f"Error encrypting data: {e}")
            raise

    def aes_decrypt(self, encrypted_data):
        """Giải mã dữ liệu AES với PKCS7 padding"""
        try:
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Giải mã
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Loại bỏ padding
            decrypted_data = self._pkcs7_unpad(decrypted_padded)
            
            # Trả về string
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            print(f"Error decrypting data: {e}")
            # Thử phương pháp cũ để tương thích ngược
            try:
                cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv), backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
                return decrypted_padded.decode('utf-8').rstrip()
            except:
                raise Exception(f"Cannot decrypt data: {e}")

    def sign_transaction(self, transaction):
        """Ký giao dịch"""
        try:
            return self.rsa_key.sign(
                json.dumps(transaction, sort_keys=True).encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
        except Exception as e:
            print(f"Error signing transaction: {e}")
            raise

    def get_public_key(self):
        """Lấy public key"""
        return self.rsa_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def verify_signature(self, transaction, signature, public_key_pem):
        """Xác minh chữ ký giao dịch"""
        try:
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            
            public_key = load_pem_public_key(public_key_pem.encode(), backend=default_backend())
            
            public_key.verify(
                signature,
                json.dumps(transaction, sort_keys=True).encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False

    def test_encryption(self):
        """Test function để kiểm tra mã hóa/giải mã"""
        test_data = "Test data for encryption 测试数据"
        print(f"Original: {test_data}")
        
        try:
            # Mã hóa
            encrypted = self.aes_encrypt(test_data)
            print(f"Encrypted length: {len(encrypted)}")
            
            # Giải mã
            decrypted = self.aes_decrypt(encrypted)
            print(f"Decrypted: {decrypted}")
            
            # Kiểm tra
            success = test_data == decrypted
            print(f"Test {'PASSED' if success else 'FAILED'}")
            return success
            
        except Exception as e:
            print(f"Test FAILED with error: {e}")
            return False