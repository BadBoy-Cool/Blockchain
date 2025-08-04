import sqlite3
import time
import json
import base64
import os
from backend.blockchain import Blockchain
from backend.smart_contract import SmartContract
from backend.crypto_utils import CryptoUtils
from backend.oracle import oracle_fetch_data

class PayrollSystem:
    def __init__(self):
        print("Initializing PayrollSystem...")
        
        # Khởi tạo các components
        self.smart_contract = SmartContract()
        self.crypto = CryptoUtils()
        
        # Khởi tạo blockchain (sẽ tự động load từ file nếu có)
        self.blockchain = Blockchain()
        
        # In thông tin blockchain sau khi khởi tạo
        self.print_blockchain_status()

    def print_blockchain_status(self):
        """In thông tin trạng thái blockchain"""
        info = self.blockchain.get_blockchain_info()
        print("=== BLOCKCHAIN STATUS ===")
        print(f"Total blocks: {info['total_blocks']}")
        print(f"Blockchain file exists: {info['file_exists']}")
        print(f"Backup file exists: {info['backup_exists']}")
        print(f"Chain valid: {info['chain_valid']}")
        print(f"Last block time: {info['last_block_time']}")
        print("========================")

    def process_payroll(self, employee_id, month):
        """Xử lý bảng lương và lưu vào blockchain"""
        try:
            print(f"Processing payroll for employee {employee_id}, month {month}")
            
            # Lấy dữ liệu từ Oracle
            work_hours, overtime_hours, kpi_score = oracle_fetch_data(employee_id, month)
            
            # Lấy thông tin nhân viên
            conn = sqlite3.connect('payroll.db')
            c = conn.cursor()
            c.execute("SELECT name, agreed_salary FROM employees WHERE id = ?", (employee_id,))
            employee_info = c.fetchone()
            conn.close()
            
            if not employee_info:
                raise Exception(f"Không tìm thấy nhân viên với ID {employee_id}")
            
            employee_name, agreed_salary = employee_info

            # Tính toán lương sử dụng smart contract
            actual_workdays = work_hours / 8 if work_hours else 0
            base_salary = self.smart_contract.calculate_base_salary(agreed_salary, actual_workdays)
            overtime_salary = self.smart_contract.calculate_overtime_salary(overtime_hours, agreed_salary)
            kpi_bonus = self.smart_contract.calculate_kpi_bonus(kpi_score)
            total_salary = self.smart_contract.calculate_total_salary(base_salary, overtime_salary, kpi_bonus)

            # Tạo transaction (bỏ phần ký giao dịch)
            transaction = {
                'employee_id': employee_id,
                'employee_name': employee_name,
                'month': month,
                'work_hours': work_hours,
                'overtime_hours': overtime_hours,
                'kpi_score': kpi_score,
                'agreed_salary': agreed_salary,
                'actual_workdays': actual_workdays,
                'base_salary': base_salary,
                'overtime_salary': overtime_salary,
                'kpi_bonus': kpi_bonus,
                'total_salary': total_salary,
                'timestamp': time.time(),
                'processed_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }

            # Mã hóa transaction để lưu vào blockchain
            transaction_json = json.dumps(transaction, ensure_ascii=False)
            encrypted_transaction = self.crypto.aes_encrypt(transaction_json)
            encrypted_transaction_b64 = base64.b64encode(encrypted_transaction).decode('utf-8')

            # Thêm transaction đã mã hóa vào pending
            self.blockchain.add_transaction(encrypted_transaction_b64)

            # Tạo block mới với tất cả pending transactions
            new_block = self.blockchain.add_block(self.blockchain.pending_transactions)
            
            print(f"Transaction processed successfully:")
            print(f"- Employee: {employee_name} (ID: {employee_id})")
            print(f"- Total salary: ${total_salary:.2f}")
            print(f"- Block index: {new_block.index}")
            print(f"- Block hash: {new_block.hash}")

            # Trả về transaction (chưa mã hóa) để hiển thị
            return transaction

        except Exception as e:
            print(f"Error processing payroll: {e}")
            raise e

    def get_employee_salary_history(self, employee_id):
        """Lấy lịch sử lương của nhân viên"""
        try:
            transactions = []
            
            for block in self.blockchain.chain:
                for tx_data in block.transactions:
                    try:
                        # Decode transaction
                        if isinstance(tx_data, str):
                            encrypted_bytes = base64.b64decode(tx_data)
                            decrypted_json = self.crypto.aes_decrypt(encrypted_bytes)
                            tx_dict = json.loads(decrypted_json)
                        else:
                            tx_dict = tx_data
                        
                        # Kiểm tra nếu là transaction của nhân viên này
                        if tx_dict.get('employee_id') == employee_id:
                            tx_dict['block_index'] = block.index
                            tx_dict['block_hash'] = block.hash
                            transactions.append(tx_dict)
                            
                    except Exception as e:
                        print(f"Error decoding transaction: {e}")
                        continue
            
            # Sắp xếp theo thời gian
            transactions.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return transactions
            
        except Exception as e:
            print(f"Error getting salary history: {e}")
            return []

    def verify_transaction(self, transaction_data):
        """Xác minh tính hợp lệ của transaction (bỏ xác minh chữ ký)"""
        try:
            # Kiểm tra các trường bắt buộc
            required_fields = ['employee_id', 'month', 'total_salary', 'timestamp']
            return all(field in transaction_data for field in required_fields)
            
        except Exception as e:
            print(f"Error verifying transaction: {e}")
            return False

    def get_all_transactions(self):
        """Lấy tất cả transactions đã decode"""
        transactions = []
        errors = []
        
        try:
            for block_index, block in enumerate(self.blockchain.chain):
                for tx_index, tx_data in enumerate(block.transactions):
                    try:
                        if isinstance(tx_data, str):
                            # Decode base64 + decrypt
                            encrypted_bytes = base64.b64decode(tx_data)
                            decrypted_json = self.crypto.aes_decrypt(encrypted_bytes)
                            tx_dict = json.loads(decrypted_json)
                        else:
                            tx_dict = tx_data
                        
                        # Thêm metadata
                        tx_dict['block_index'] = block_index
                        tx_dict['block_hash'] = block.hash
                        tx_dict['block_timestamp'] = block.timestamp
                        
                        transactions.append(tx_dict)
                        
                    except Exception as e:
                        error_info = {
                            'block_index': block_index,
                            'transaction_index': tx_index,
                            'error': str(e),
                            'raw_data': str(tx_data)[:100] + '...' if len(str(tx_data)) > 100 else str(tx_data)
                        }
                        errors.append(error_info)
        
        except Exception as e:
            print(f"Error getting all transactions: {e}")
        
        return transactions, errors

    def backup_blockchain(self):
        """Tạo backup thủ công"""
        try:
            self.blockchain.backup_chain()
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def restore_blockchain(self):
        """Khôi phục blockchain từ backup"""
        try:
            return self.blockchain.restore_from_backup()
        except Exception as e:
            print(f"Error restoring blockchain: {e}")
            return False

    def get_system_stats(self):
        """Lấy thống kê hệ thống"""
        try:
            blockchain_stats = self.blockchain.get_blockchain_stats()
            blockchain_info = self.blockchain.get_blockchain_info()
            
            # Đếm transactions và tính tổng lương
            transactions, errors = self.get_all_transactions()
            total_salary = sum(tx.get('total_salary', 0) for tx in transactions if isinstance(tx.get('total_salary'), (int, float)))
            
            # Thống kê nhân viên
            conn = sqlite3.connect('payroll.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM employees")
            total_employees = c.fetchone()[0]
            conn.close()
            
            return {
                'blockchain': blockchain_stats,
                'blockchain_info': blockchain_info,
                'total_transactions': len(transactions),
                'total_salary': total_salary,
                'total_employees': total_employees,
                'decoding_errors': len(errors),
                'last_processed': max([tx.get('timestamp', 0) for tx in transactions]) if transactions else 0
            }
            
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {}