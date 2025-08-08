import sqlite3

def add_country_column():
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()

    # Kiểm tra cột country đã tồn tại chưa
    c.execute("PRAGMA table_info(employees)")
    columns = [col[1] for col in c.fetchall()]
    
    if "country" not in columns:
        # Thêm cột country (KHÔNG mặc định VN nữa)
        c.execute("ALTER TABLE employees ADD COLUMN country TEXT")
        print("✅ Đã thêm cột 'country' vào bảng employees.")
    else:
        print("ℹ️ Cột 'country' đã tồn tại.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_country_column()
