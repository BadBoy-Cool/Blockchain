import sqlite3
import json
import base64
from datetime import datetime
import io

class ReportGenerator:
    def __init__(self):
        pass
    
    def get_salary_statistics(self):
        """Lấy thống kê lương chi tiết - Version 3 with better debugging"""
        try:
            from backend.payroll_system import PayrollSystem
            payroll_system = PayrollSystem()
            
            # Debug: In ra thông tin blockchain
            print(f"Debug - Total blocks: {len(payroll_system.blockchain.chain)}")
            
            # Lấy dữ liệu từ blockchain
            total_salary = 0
            total_transactions = 0
            transaction_details = []
            decoding_errors = []
            
            for block_index, block in enumerate(payroll_system.blockchain.chain):
                print(f"Debug - Block {block_index}: {len(block.transactions)} transactions")
                
                for tx_index, tx_data in enumerate(block.transactions):
                    try:
                        tx_dict = None
                        
                        # Kiểm tra kiểu dữ liệu và decode
                        if isinstance(tx_data, str):
                            print(f"Debug - Processing string transaction: {tx_data[:50]}...")
                            
                            # Thử decode base64 + decrypt trước
                            try:
                                encrypted_bytes = base64.b64decode(tx_data)
                                decrypted_json = payroll_system.crypto.aes_decrypt(encrypted_bytes)
                                tx_dict = json.loads(decrypted_json)
                                print(f"Debug - Successfully decrypted transaction")
                            except Exception as decode_error:
                                print(f"Debug - Decode error: {decode_error}")
                                
                                # Thử parse JSON trực tiếp
                                try:
                                    tx_dict = json.loads(tx_data)
                                    print(f"Debug - Parsed as direct JSON")
                                except Exception as json_error:
                                    print(f"Debug - JSON parse error: {json_error}")
                                    decoding_errors.append(f"Block {block_index}, TX {tx_index}: Decode failed - {str(decode_error)}")
                                    continue
                                    
                        elif isinstance(tx_data, dict):
                            # Dữ liệu đã là dictionary
                            tx_dict = tx_data
                            print(f"Debug - Transaction is already a dict")
                            
                        else:
                            # Kiểu dữ liệu khác
                            print(f"Debug - Unknown transaction type: {type(tx_data)}")
                            try:
                                tx_dict = json.loads(str(tx_data))
                            except:
                                decoding_errors.append(f"Block {block_index}, TX {tx_index}: Unknown data type {type(tx_data)}")
                                continue
                        
                        # Xử lý transaction đã decode
                        if tx_dict and isinstance(tx_dict, dict):
                            print(f"Debug - Transaction dict: {tx_dict}")
                            
                            # Kiểm tra các trường bắt buộc
                            if 'total_salary' in tx_dict:
                                salary = tx_dict.get('total_salary', 0)
                                
                                # Đảm bảo salary là số
                                try:
                                    salary = float(salary)
                                    if salary > 0:
                                        total_salary += salary
                                        total_transactions += 1
                                        transaction_details.append(tx_dict)
                                        print(f"Debug - Added transaction: ${salary}")
                                    else:
                                        print(f"Debug - Invalid salary value: {salary}")
                                except (ValueError, TypeError):
                                    print(f"Debug - Cannot convert salary to float: {salary}")
                                    decoding_errors.append(f"Block {block_index}, TX {tx_index}: Invalid salary value")
                            else:
                                print(f"Debug - Transaction missing total_salary field")
                                decoding_errors.append(f"Block {block_index}, TX {tx_index}: Missing total_salary field")
                        else:
                            print(f"Debug - Failed to get valid transaction dict")
                            decoding_errors.append(f"Block {block_index}, TX {tx_index}: Failed to parse transaction")
                            
                    except Exception as e:
                        decoding_errors.append(f"Block {block_index}, TX {tx_index}: {str(e)}")
                        print(f"Debug - Transaction processing error: {e}")
                        continue
            
            print(f"Debug - Final totals - Salary: ${total_salary}, Transactions: {total_transactions}")
            print(f"Debug - Decoding errors: {len(decoding_errors)}")
            
            # Lấy thống kê từ database
            conn = sqlite3.connect('payroll.db')
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM employees")
            total_employees = c.fetchone()[0]
            
            c.execute("SELECT AVG(kpi_score) FROM kpi WHERE kpi_score IS NOT NULL")
            avg_kpi_result = c.fetchone()[0]
            avg_kpi = avg_kpi_result if avg_kpi_result else 0
            
            # Lấy thống kê chi tiết từ database theo tháng
            c.execute("""SELECT 
                        strftime('%Y-%m', date) as month,
                        COUNT(DISTINCT employee_id) as employees,
                        AVG(kpi_score) as avg_kpi,
                        COUNT(*) as kpi_records
                        FROM kpi 
                        WHERE date IS NOT NULL
                        GROUP BY strftime('%Y-%m', date)
                        ORDER BY month""")
            
            monthly_db_stats = {}
            for row in c.fetchall():
                if row[0]:  # month không null
                    monthly_db_stats[row[0]] = {
                        'employees': row[1],
                        'avg_kpi': row[2] or 0,
                        'kpi_records': row[3]
                    }
            
            conn.close()
            
            # Thống kê blockchain
            try:
                blockchain_stats = payroll_system.blockchain.get_blockchain_stats()
            except Exception as e:
                print(f"Debug - Blockchain stats error: {e}")
                blockchain_stats = {
                    'total_blocks': len(payroll_system.blockchain.chain),
                    'chain_valid': True,
                    'total_size_bytes': 0
                }
            
            # Lấy thống kê theo tháng từ blockchain
            monthly_blockchain_stats = {}
            try:
                monthly_blockchain_stats = payroll_system.blockchain.get_transaction_volume_by_month()
                print(f"Debug - Monthly blockchain stats: {monthly_blockchain_stats}")
            except Exception as e:
                print(f"Debug - Monthly blockchain stats error: {e}")
            
            result = {
                'total_salary': total_salary,
                'total_employees': total_employees,
                'total_transactions': total_transactions,
                'avg_kpi': avg_kpi,
                'total_blocks': blockchain_stats.get('total_blocks', 0),
                'chain_valid': blockchain_stats.get('chain_valid', True),
                'total_size_bytes': blockchain_stats.get('total_size_bytes', 0),
                'transaction_details': transaction_details,
                'decoding_errors': decoding_errors,
                'monthly_db_stats': monthly_db_stats,
                'monthly_blockchain_stats': monthly_blockchain_stats
            }
            
            print(f"Debug - Final result: {result}")
            return result
            
        except Exception as e:
            print(f"Error getting salary statistics: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: Lấy dữ liệu cơ bản từ database
            try:
                conn = sqlite3.connect('payroll.db')
                c = conn.cursor()
                
                c.execute("SELECT COUNT(*) FROM employees")
                total_employees = c.fetchone()[0]
                
                c.execute("SELECT AVG(kpi_score) FROM kpi")
                avg_kpi_result = c.fetchone()[0]
                avg_kpi = avg_kpi_result if avg_kpi_result else 0
                
                conn.close()
                
                return {
                    'total_salary': 0,
                    'total_employees': total_employees,
                    'total_transactions': 0,
                    'avg_kpi': avg_kpi,
                    'total_blocks': 0,
                    'chain_valid': False,
                    'total_size_bytes': 0,
                    'transaction_details': [],
                    'decoding_errors': [f"System error: {str(e)}"],
                    'monthly_db_stats': {},
                    'monthly_blockchain_stats': {}
                }
            except:
                return {
                    'total_salary': 0,
                    'total_employees': 0,
                    'total_transactions': 0,
                    'avg_kpi': 0,
                    'total_blocks': 0,
                    'chain_valid': False,
                    'total_size_bytes': 0,
                    'transaction_details': [],
                    'decoding_errors': [f"Critical error: {str(e)}"],
                    'monthly_db_stats': {},
                    'monthly_blockchain_stats': {}
                }
    
    def generate_salary_report_pdf(self):
        """Tạo báo cáo lương dạng PDF với dữ liệu thực"""
        try:
            stats = self.get_salary_statistics()
            
            # Tạo nội dung báo cáo chi tiết
            content = f"""SALARY REPORT - PAYROLL BLOCKCHAIN SYSTEM
==============================================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY STATISTICS:
==================
Total Salary Paid: ${stats['total_salary']:.2f}
Total Employees: {stats['total_employees']}
Total Transactions: {stats['total_transactions']}
Average KPI Score: {stats['avg_kpi']:.1f}

BLOCKCHAIN STATISTICS:
=====================
Total Blocks: {stats.get('total_blocks', 0)}
Chain Valid: {'✅ Yes' if stats.get('chain_valid') else '❌ No'}
Total Size: {stats.get('total_size_bytes', 0)} bytes

DETAILED TRANSACTIONS:
====================
"""
            
            # Thêm chi tiết giao dịch
            if stats['transaction_details']:
                for i, tx in enumerate(stats['transaction_details'], 1):
                    content += f"""
Transaction #{i}:
Employee ID: {tx.get('employee_id', 'N/A')}
Month: {tx.get('month', 'N/A')}
Base Salary: ${tx.get('base_salary', 0):.2f}
Overtime: ${tx.get('overtime_salary', 0):.2f}
KPI Bonus: ${tx.get('kpi_bonus', 0):.2f}
Total: ${tx.get('total_salary', 0):.2f}
Date: {datetime.fromtimestamp(tx.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}
-------------------------------------------
"""
            else:
                content += "\nNo transactions found in blockchain.\n"
            
            # Thêm thông tin lỗi nếu có
            if stats['decoding_errors']:
                content += f"""
DECODING ERRORS:
===============
{chr(10).join(stats['decoding_errors'])}
"""
            
            content += f"""
==============================================
Report generated by Blockchain Payroll System
==============================================
"""
            
            # Tạo buffer
            buffer = io.BytesIO()
            buffer.write(content.encode('utf-8'))
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            # Fallback nếu có lỗi
            error_content = f"""ERROR GENERATING REPORT
============================
Error: {str(e)}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the system logs for more details.
============================"""
            buffer = io.BytesIO()
            buffer.write(error_content.encode('utf-8'))
            buffer.seek(0)
            return buffer
    
    def generate_salary_report_excel(self):
        """Tạo báo cáo lương dạng Excel với dữ liệu thực"""
        try:
            stats = self.get_salary_statistics()
            
            # Tạo nội dung CSV-like cho Excel
            content = f"""SALARY REPORT - EXCEL FORMAT
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
Total Salary,${stats['total_salary']:.2f}
Total Employees,{stats['total_employees']}
Total Transactions,{stats['total_transactions']}
Average KPI,{stats['avg_kpi']:.1f}

TRANSACTIONS:
Employee ID,Month,Base Salary,Overtime,KPI Bonus,Total Salary,Date
"""
            
            # Thêm dữ liệu giao dịch
            if stats['transaction_details']:
                for tx in stats['transaction_details']:
                    content += f"{tx.get('employee_id', 'N/A')},{tx.get('month', 'N/A')},{tx.get('base_salary', 0):.2f},{tx.get('overtime_salary', 0):.2f},{tx.get('kpi_bonus', 0):.2f},{tx.get('total_salary', 0):.2f},{datetime.fromtimestamp(tx.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n"
            else:
                content += "No transaction data available\n"
            
            buffer = io.BytesIO()
            buffer.write(content.encode('utf-8'))
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            error_content = f"Error generating Excel report: {str(e)}"
            buffer = io.BytesIO()
            buffer.write(error_content.encode('utf-8'))
            buffer.seek(0)
            return buffer