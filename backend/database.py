import sqlite3
from backend.crypto_utils import CryptoUtils

def init_db():
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()

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

    #Tạo bảng users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user',
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            employee_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''')

    #Khởi tạo Crypto để sinh public key
    crypto = CryptoUtils()
    public_key = crypto.get_public_key()

    #Thêm nhân viên mẫu
    c.execute('''
        INSERT OR IGNORE INTO employees (id, name, agreed_salary, public_key)
        VALUES (?, ?, ?, ?)
    ''', (1, "Nguyễn Văn A", 1000, public_key))

    #Thêm dữ liệu chấm công và KPI
    c.execute('''
        INSERT OR IGNORE INTO attendance (employee_id, date, hours_worked, overtime_hours)
        VALUES (?, ?, ?, ?)
    ''', (1, "2025-07-01", 160, 10))

    c.execute('''
        INSERT OR IGNORE INTO kpi (employee_id, date, kpi_score)
        VALUES (?, ?, ?)
    ''', (1, "2025-07-01", 85))

    #Thêm tài khoản admin mặc định (không gắn với employee_id)
    c.execute('''
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, ?)
    ''', ('admin', 'admin123', 'admin'))

    #Thêm tài khoản user gắn với employee_id = 1
    c.execute('''
        INSERT OR IGNORE INTO users (username, password, role, employee_id)
        VALUES (?, ?, ?, ?)
    ''', ('nv1', 'nvpass123', 'user', 1))

    conn.commit()
    conn.close()
