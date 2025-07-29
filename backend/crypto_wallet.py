import requests
import json
from decimal import Decimal
import sqlite3
from datetime import datetime

class CryptoWallet:
    def __init__(self):
        self.base_url = "https://api.coinbase.com/v2"  # API mô phỏng
        self.init_wallet_db()
    
    def init_wallet_db(self):
        """Khởi tạo bảng ví crypto"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS crypto_wallets
                     (id INTEGER PRIMARY KEY,
                      employee_id INTEGER,
                      wallet_address TEXT,
                      balance REAL DEFAULT 0.0,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (employee_id) REFERENCES employees (id))''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS crypto_transactions
                     (id INTEGER PRIMARY KEY,
                      wallet_id INTEGER,
                      transaction_hash TEXT,
                      amount REAL,
                      transaction_type TEXT,
                      status TEXT DEFAULT 'pending',
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (wallet_id) REFERENCES crypto_wallets (id))''')
        
        conn.commit()
        conn.close()
    
    def create_wallet(self, employee_id):
        """Tạo ví crypto cho nhân viên"""
        # Mô phỏng tạo địa chỉ ví
        import secrets
        wallet_address = "0x" + secrets.token_hex(20)
        
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        c.execute("INSERT INTO crypto_wallets (employee_id, wallet_address) VALUES (?, ?)",
                 (employee_id, wallet_address))
        wallet_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'wallet_id': wallet_id,
            'address': wallet_address,
            'balance': 0.0
        }
    
    def send_salary(self, employee_id, amount_usd):
        """Gửi lương qua crypto (mô phỏng)"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        # Lấy thông tin ví
        c.execute("SELECT id, wallet_address, balance FROM crypto_wallets WHERE employee_id = ?", (employee_id,))
        wallet_info = c.fetchone()
        
        if not wallet_info:
            # Tạo ví mới nếu chưa có
            wallet = self.create_wallet(employee_id)
            wallet_id = wallet['wallet_id']
            wallet_address = wallet['address']
            current_balance = 0.0
        else:
            wallet_id, wallet_address, current_balance = wallet_info
        
        # Mô phỏng giao dịch crypto
        tx_hash = "0x" + secrets.token_hex(32)
        
        # Cập nhật balance
        new_balance = current_balance + amount_usd
        c.execute("UPDATE crypto_wallets SET balance = ? WHERE id = ?", (new_balance, wallet_id))
        
        # Lưu giao dịch
        c.execute("""INSERT INTO crypto_transactions 
                     (wallet_id, transaction_hash, amount, transaction_type, status) 
                     VALUES (?, ?, ?, ?, ?)""",
                 (wallet_id, tx_hash, amount_usd, 'salary_payment', 'completed'))
        
        conn.commit()
        conn.close()
        
        return {
            'status': 'success',
            'transaction_hash': tx_hash,
            'wallet_address': wallet_address,
            'amount': amount_usd,
            'new_balance': new_balance
        }
    
    def get_wallet_info(self, employee_id):
        """Lấy thông tin ví của nhân viên"""
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        c.execute("""SELECT w.wallet_address, w.balance, 
                           COUNT(ct.id) as transaction_count,
                           SUM(ct.amount) as total_received
                     FROM crypto_wallets w
                     LEFT JOIN crypto_transactions ct ON w.id = ct.wallet_id
                     WHERE w.employee_id = ?
                     GROUP BY w.id""", (employee_id,))
        
        result = c.fetchone()
        conn.close()
        
        if result:
            return {
                'wallet_address': result[0],
                'balance': result[1],
                'transaction_count': result[2] or 0,
                'total_received': result[3] or 0.0
            }
        return None