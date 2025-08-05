import hashlib
import json

private_key = 'e0084ddb0cafc4e5a608fbb5b790dc7a57e92f3fb1713553e6b76f8d0142ecc7'

# Tính toán SHA-256 hash
hash_key = hashlib.sha256(private_key.encode()).hexdigest()

# Ghi ra file JSON
data = {
    "admin_private_key_hash": hash_key
}

with open("crypto_keys.json", "w") as f:
    json.dump(data, f, indent=4)

print("Đã lưu hash khóa riêng vào crypto_keys.json:")
print("Hash:", hash_key)
