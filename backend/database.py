import sqlite3
from backend.crypto_utils import CryptoUtils

def init_db():
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees
                 (id INTEGER PRIMARY KEY, name TEXT, agreed_salary REAL, public_key TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (employee_id INTEGER, date TEXT, hours_worked REAL, overtime_hours REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS kpi
                 (employee_id INTEGER, date TEXT, kpi_score REAL)''')
    # Thêm dữ liệu mẫu
    crypto = CryptoUtils()
    c.execute("INSERT OR IGNORE INTO employees (id, name, agreed_salary, public_key) VALUES (?, ?, ?, ?)",
              (1, "Nguyễn Văn A", 1000, crypto.get_public_key()))
    c.execute("INSERT OR IGNORE INTO attendance (employee_id, date, hours_worked, overtime_hours) VALUES (?, ?, ?, ?)",
              (1, "2025-07-01", 160, 10))
    c.execute("INSERT OR IGNORE INTO kpi (employee_id, date, kpi_score) VALUES (?, ?, ?)",
              (1, "2025-07-01", 85))
    conn.commit()
    conn.close()