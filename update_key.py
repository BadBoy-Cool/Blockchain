import sqlite3
import json
import os

def update_public_key(username):
    filename = f"user_{username}_keys.json"
    if not os.path.exists(filename):
        print(f"❌ Không tìm thấy file {filename}")
        return

    with open(filename, "r") as f:
        keys = json.load(f)

    public_key = keys.get("public_key")
    if not public_key:
        print(f"❌ Không tìm thấy public_key trong file {filename}")
        return

    conn = sqlite3.connect("payroll.db")
    c = conn.cursor()

    # Kiểm tra xem user có tồn tại trong bảng users chưa
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = c.fetchone()

    if result:
        c.execute("UPDATE users SET public_key = ? WHERE username = ?", (public_key, username))
        print(f"✅ Đã cập nhật public_key cho user '{username}'")
    else:
        print(f"⚠️ User '{username}' chưa tồn tại trong DB, bỏ qua không cập nhật")

    conn.commit()
    conn.close()

# Danh sách các user cần cập nhật
usernames = ["admin", "duyen", "bao", "son"]

# Chạy cập nhật cho từng user
for username in usernames:
    update_public_key(username)
