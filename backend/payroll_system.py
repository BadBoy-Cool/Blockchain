import sqlite3
import time
import json
import base64
from backend.blockchain import Blockchain
from backend.smart_contract import SmartContract
from backend.crypto_utils import CryptoUtils
from backend.oracle import oracle_fetch_data

class PayrollSystem:
    def __init__(self):
        self.blockchain = Blockchain()
        self.smart_contract = SmartContract()
        self.crypto = CryptoUtils()

    def process_payroll(self, employee_id, month):
        # Lấy dữ liệu từ Oracle
        work_hours, overtime_hours, kpi_score = oracle_fetch_data(employee_id, month)
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute("SELECT agreed_salary FROM employees WHERE id = ?", (employee_id,))
        agreed_salary = c.fetchone()[0]
        conn.close()

        # Tính toán lương
        actual_workdays = work_hours / 8
        base_salary = self.smart_contract.calculate_base_salary(agreed_salary, actual_workdays)
        overtime_salary = self.smart_contract.calculate_overtime_salary(overtime_hours, agreed_salary)
        kpi_bonus = self.smart_contract.calculate_kpi_bonus(kpi_score)
        total_salary = self.smart_contract.calculate_total_salary(base_salary, overtime_salary, kpi_bonus)

        # Tạo transaction dạng dict
        transaction = {
            'employee_id': employee_id,
            'month': month,
            'base_salary': base_salary,
            'overtime_salary': overtime_salary,
            'kpi_bonus': kpi_bonus,
            'total_salary': total_salary,
            'timestamp': time.time()
        }

        # Ký giao dịch (signature dạng hex string)
        transaction['signature'] = self.crypto.sign_transaction(transaction).hex()

        # Chuyển transaction dict thành JSON string
        transaction_json = json.dumps(transaction)

        # Mã hóa transaction JSON
        encrypted_transaction = self.crypto.aes_encrypt(transaction_json)
        encrypted_transaction_b64 = base64.b64encode(encrypted_transaction).decode('utf-8')

        # Lưu cả hai: plaintext JSON (để hiển thị) và mã hóa (để blockchain)
        # Ở đây bạn có thể tùy chọn lưu gì vào blockchain. Ví dụ: lưu mã hóa
        self.blockchain.add_transaction(encrypted_transaction_b64)

        # Thêm block mới với tất cả giao dịch pending
        self.blockchain.add_block(self.blockchain.pending_transactions)

        # Trả về cả bản transaction dict (chưa mã hóa) cho view dễ dùng
        return transaction
