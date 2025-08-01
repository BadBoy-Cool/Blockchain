import ecdsa
import hashlib
import os
import base64

class Wallet:
    def __init__(self, private_key_hex=None):
        if private_key_hex:
            self.private_key = ecdsa.SigningKey.from_string(bytes.fromhex(private_key_hex), curve=ecdsa.SECP256k1)
        else:
            self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()

    @staticmethod
    def generate():
        return Wallet()

    def get_private_key_hex(self):
        return self.private_key.to_string().hex()

    def get_public_key_hex(self):
        return self.public_key.to_string().hex()

    def get_address(self):
        pub_bytes = self.public_key.to_string()
        pub_hash = hashlib.sha256(pub_bytes).hexdigest()
        return '0x' + pub_hash[-40:]  # lấy 40 ký tự cuối như địa chỉ ví

    def sign(self, message: str) -> str:
        message_bytes = message.encode('utf-8')
        signature = self.private_key.sign(message_bytes)
        return base64.b64encode(signature).decode('utf-8')

    def verify(self, message: str, signature_b64: str) -> bool:
        try:
            message_bytes = message.encode('utf-8')
            signature = base64.b64decode(signature_b64)
            return self.public_key.verify(signature, message_bytes)
        except Exception:
            return False

    def save_keys_to_file(self, filename='wallet_keys.txt'):
        with open(filename, 'w') as f:
            f.write('Private key: ' + self.get_private_key_hex() + '\n')
            f.write('Public key : ' + self.get_public_key_hex() + '\n')
            f.write('Address    : ' + self.get_address() + '\n')

    @staticmethod
    def load_from_file(filename='wallet_keys.txt'):
        with open(filename, 'r') as f:
            lines = f.readlines()
        private_hex = lines[0].split(': ')[1].strip()
        return Wallet(private_hex)


if __name__ == "__main__":
    wallet = Wallet.generate()
    print("Private key:", wallet.get_private_key_hex())
    print("Public key :", wallet.get_public_key_hex())
    print("Address    :", wallet.get_address())
    wallet.save_keys_to_file()
