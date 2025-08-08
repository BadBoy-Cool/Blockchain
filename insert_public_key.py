import sqlite3
import json
import os

def insert_public_key_to_db(username):
    filename = f"user_{username}_keys.json"
    if not os.path.exists(filename):
        print(f"Không tìm thấy file {filename}")
        return

    with open(filename, 'r') as f:
        keys = json.load(f)

    public_key = keys.get('public_key')
    if not public_key:
        print(f"Không tìm thấy public_key trong {filename}")
        return

    conn = sqlite3.connect("payroll.db")
    c = conn.cursor()

    # Kiểm tra nếu user đã tồn tại để chỉ UPDATE
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = c.fetchone()

    if result:
        # Đã có user → UPDATE khóa
        c.execute("UPDATE users SET public_key = ? WHERE username = ?", (public_key, username))
        print(f"Cập nhật public_key cho user '{username}'")
    else:
        # Chưa có user → INSERT mới (nếu muốn)
        c.execute("INSERT INTO users (username, public_key) VALUES (?, ?)", (username, public_key))
        print(f"Thêm mới user '{username}' kèm public_key")

    conn.commit()
    conn.close()

# Danh sách các user cần xử lý
usernames = ["admin", "duyen", "bao", "son","linh"]

#Chạy vòng lặp
for username in usernames:
    insert_public_key_to_db(username)
