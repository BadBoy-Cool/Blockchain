import hashlib
import secrets
import sqlite3
from functools import wraps
from flask import session, request, redirect, url_for, flash

class AuthSystem:
    def __init__(self):
        self.init_auth_db()

    def init_auth_db(self):
        """Khởi tạo bảng users"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        # Tạo bảng users
        c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY, 
              username TEXT UNIQUE, 
              password_hash TEXT, 
              salt TEXT,
              role TEXT DEFAULT 'user',
              employee_id INTEGER,  -- THÊM DÒNG NÀY
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              last_login TIMESTAMP,
              is_active BOOLEAN DEFAULT 1)''')

        
        # Tạo bảng sessions
        c.execute('''CREATE TABLE IF NOT EXISTS user_sessions
                     (id INTEGER PRIMARY KEY,
                      user_id INTEGER,
                      session_token TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      expires_at TIMESTAMP,
                      is_active BOOLEAN DEFAULT 1,
                      FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Tạo admin mặc định nếu chưa có
        c.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        if c.fetchone()[0] == 0:
            self.create_user('admin', 'admin123', 'admin')
            print("Tạo tài khoản admin mặc định - Username: admin, Password: admin123")
        
        conn.commit()
        conn.close()

    def hash_password(self, password, salt=None):
        """Hash password với salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return password_hash.hex(), salt

    def create_user(self, username, password, role='user'):
        """Tạo user mới"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        try:
            password_hash, salt = self.hash_password(password)
            c.execute("INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
                     (username, password_hash, salt, role))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            return {'success': True, 'user_id': user_id}
        except sqlite3.IntegrityError:
            conn.close()
            return {'success': False, 'error': 'Username đã tồn tại'}

    def verify_user(self, username, password):
        """Xác thực user"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        # Thêm employee_id vào SELECT
        c.execute("SELECT id, password_hash, salt, role, is_active, employee_id FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
        if not user or not user[4]:  # user không tồn tại hoặc bị deactive
            conn.close()
            return None
            
        user_id, stored_hash, salt, role, is_active, employee_id = user
        password_hash, _ = self.hash_password(password, salt)
        
        if password_hash == stored_hash:
            # Cập nhật last_login
            c.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            return {
                'id': user_id,
                'username': username,
                'role': role,
                'employee_id': employee_id 
            }
        
        conn.close()
        return None


    def get_all_users(self):
        """Lấy danh sách tất cả users"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute("SELECT id, username, role, created_at, last_login, is_active FROM users ORDER BY created_at DESC")
        users = c.fetchall()
        conn.close()
        return users

    def change_password(self, user_id, new_password):
        """Đổi mật khẩu"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        password_hash, salt = self.hash_password(new_password)
        c.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                 (password_hash, salt, user_id))
        conn.commit()
        conn.close()
        return True

    def deactivate_user(self, user_id):
        """Vô hiệu hóa user"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True

# Decorator cho việc yêu cầu đăng nhập
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator cho việc yêu cầu quyền admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục', 'error')
            return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            flash('Bạn không có quyền truy cập chức năng này', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

