import sqlite3
from backend.crypto_utils import CryptoUtils

def init_db():
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()

    c.execute('DROP TABLE IF EXISTS users')

    # Tạo bảng employees
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            agreed_salary REAL,
            public_key TEXT
        )
    ''')

    # Tạo bảng attendance
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            employee_id INTEGER,
            date TEXT,
            hours_worked REAL,
            overtime_hours REAL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    # Tạo bảng kpi
    c.execute('''
        CREATE TABLE IF NOT EXISTS kpi (
            employee_id INTEGER,
            date TEXT,
            kpi_score REAL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    # Tạo bảng users (bỏ password, thêm public_key)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            public_key TEXT,
            role TEXT DEFAULT 'user',
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            employee_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    # Khởi tạo Crypto để sinh public key
    crypto = CryptoUtils()
    public_key = crypto.get_public_key()

    conn.commit()
    conn.close()