#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE TEST SUITE FOR PAYROLL BLOCKCHAIN SYSTEM
Automated testing script để test toàn bộ hệ thống payroll blockchain
"""

import unittest
import requests
import json
import sqlite3
import os
import time
import base64
from datetime import datetime
import sys

class PayrollSystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {}
        
    def log_result(self, test_name, status, message=""):
        """Ghi lại kết quả test"""
        self.test_results[test_name] = {
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        print(f"{'✅' if status else '❌'} {test_name}: {message}")
    
    def test_server_running(self):
        """Test 1: Kiểm tra server có chạy không"""
        try:
            response = self.session.get(f"{self.base_url}/login", timeout=5)
            if response.status_code == 200:
                self.log_result("Server Running", True, "Server accessible")
                return True
            else:
                self.log_result("Server Running", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Server Running", False, f"Connection error: {str(e)}")
            return False
    
    def test_database_setup(self):
        """Test 2: Kiểm tra database được tạo đúng"""
        try:
            if not os.path.exists('payroll.db'):
                self.log_result("Database Setup", False, "payroll.db not found")
                return False
            
            conn = sqlite3.connect('payroll.db')
            c = conn.cursor()
            
            # Kiểm tra các bảng cần thiết
            required_tables = ['employees', 'attendance', 'kpi', 'users']
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in c.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                self.log_result("Database Setup", False, f"Missing tables: {missing_tables}")
                return False
            
            # Kiểm tra admin user có tồn tại
            c.execute("SELECT username FROM users WHERE role='admin'")
            admin_exists = c.fetchone() is not None
            
            conn.close()
            
            if admin_exists:
                self.log_result("Database Setup", True, "All tables and admin user exist")
                return True
            else:
                self.log_result("Database Setup", False, "Admin user not found")
                return False
                
        except Exception as e:
            self.log_result("Database Setup", False, f"Database error: {str(e)}")
            return False
    
    def test_authentication(self):
        """Test 3: Kiểm tra hệ thống đăng nhập"""
        try:
            # Test login thành công
            login_data = {'username': 'admin', 'password': 'admin123'}
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            
            if response.status_code == 200 and 'dashboard' in response.url or response.url.endswith('/'):
                self.log_result("Login Success", True, "Admin login successful")
                login_success = True
            else:
                self.log_result("Login Success", False, f"Login failed: {response.status_code}")
                login_success = False
            
            # Test login thất bại
            wrong_login = {'username': 'wrong', 'password': 'wrong'}
            response2 = self.session.post(f"{self.base_url}/login", data=wrong_login)
            
            if 'login' in response2.url:
                self.log_result("Login Failure", True, "Wrong credentials properly rejected")
            else:
                self.log_result("Login Failure", False, "Security issue: wrong login accepted")
            
            return login_success
            
        except Exception as e:
            self.log_result("Authentication", False, f"Auth error: {str(e)}")
            return False
    
    def test_employee_management(self):
        """Test 4: Kiểm tra quản lý nhân viên"""
        try:
            # Test thêm nhân viên
            employee_data = {
                'name': 'Test Employee Auto',
                'salary': '1500'
            }
            
            response = self.session.post(f"{self.base_url}/add_employee", data=employee_data)
            
            if response.status_code == 200:
                result = response.json()
                if 'employee_id' in result:
                    self.employee_id = result['employee_id']
                    self.log_result("Add Employee", True, f"Employee added with ID: {self.employee_id}")
                    
                    # Verify trong database
                    conn = sqlite3.connect('payroll.db')
                    c = conn.cursor()
                    c.execute("SELECT name, agreed_salary FROM employees WHERE id=?", (self.employee_id,))
                    emp_data = c.fetchone()
                    conn.close()
                    
                    if emp_data and emp_data[0] == 'Test Employee Auto':
                        self.log_result("Employee DB Verification", True, "Employee saved correctly")
                        return True
                    else:
                        self.log_result("Employee DB Verification", False, "Employee not saved properly")
                        return False
                else:
                    self.log_result("Add Employee", False, "No employee_id returned")
                    return False
            else:
                self.log_result("Add Employee", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Employee Management", False, f"Error: {str(e)}")
            return False
    
    def test_attendance_kpi_input(self):
        """Test 5: Kiểm tra nhập dữ liệu chấm công/KPI"""
        try:
            if not hasattr(self, 'employee_id'):
                # Tạo employee mới nếu chưa có
                self.test_employee_management()
            
            attendance_data = {
                'employee_id': str(self.employee_id),
                'date': '2025-07-01',
                'hours_worked': '160',
                'overtime_hours': '10',
                'kpi_score': '85'
            }
            
            response = self.session.post(f"{self.base_url}/add_data", data=attendance_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    self.log_result("Add Attendance/KPI", True, "Data added successfully")
                    
                    # Verify trong database
                    conn = sqlite3.connect('payroll.db')
                    c = conn.cursor()
                    c.execute("SELECT hours_worked FROM attendance WHERE employee_id=? AND date=?", 
                             (self.employee_id, '2025-07-01'))
                    att_data = c.fetchone()
                    
                    c.execute("SELECT kpi_score FROM kpi WHERE employee_id=? AND date=?",
                             (self.employee_id, '2025-07-01'))
                    kpi_data = c.fetchone()
                    conn.close()
                    
                    if att_data and kpi_data:
                        self.log_result("Attendance/KPI DB Verification", True, "Data saved correctly")
                        return True
                    else:
                        self.log_result("Attendance/KPI DB Verification", False, "Data not saved")
                        return False
                else:
                    self.log_result("Add Attendance/KPI", False, f"API returned: {result}")
                    return False
            else:
                self.log_result("Add Attendance/KPI", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Attendance/KPI Input", False, f"Error: {str(e)}")
            return False
    
    def test_payroll_processing(self):
        """Test 6: Kiểm tra xử lý bảng lương và blockchain"""
        try:
            if not hasattr(self, 'employee_id'):
                self.test_employee_management()
                self.test_attendance_kpi_input()
            
            payroll_data = {
                'employee_id': str(self.employee_id),
                'month': '2025-07'
            }
            
            response = self.session.post(f"{self.base_url}/process_payroll", data=payroll_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    transaction = result.get('transaction', {})
                    
                    # Kiểm tra các trường cần thiết
                    required_fields = ['employee_id', 'base_salary', 'overtime_salary', 
                                     'kpi_bonus', 'total_salary', 'signature']
                    
                    missing_fields = [field for field in required_fields if field not in transaction]
                    
                    if not missing_fields:
                        # Kiểm tra công thức tính toán
                        base_salary = transaction['base_salary']
                        overtime_salary = transaction['overtime_salary']
                        kpi_bonus = transaction['kpi_bonus']
                        total_salary = transaction['total_salary']
                        
                        calculated_total = base_salary + overtime_salary + kpi_bonus
                        
                        if abs(calculated_total - total_salary) < 0.01:  # Floating point precision
                            self.log_result("Payroll Calculation", True, 
                                          f"Total: ${total_salary:.2f} calculated correctly")
                            
                            # Kiểm tra signature có được tạo
                            if transaction.get('signature') and len(transaction['signature']) > 50:
                                self.log_result("Digital Signature", True, "Signature generated")
                                return True
                            else:
                                self.log_result("Digital Signature", False, "Invalid signature")
                                return False
                        else:
                            self.log_result("Payroll Calculation", False, 
                                          f"Math error: {calculated_total} vs {total_salary}")
                            return False
                    else:
                        self.log_result("Payroll Processing", False, f"Missing fields: {missing_fields}")
                        return False
                else:
                    self.log_result("Payroll Processing", False, f"API error: {result}")
                    return False
            else:
                self.log_result("Payroll Processing", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Payroll Processing", False, f"Error: {str(e)}")
            return False
    
    def test_blockchain_integrity(self):
        """Test 7: Kiểm tra tính toàn vẹn blockchain"""
        try:
            response = self.session.get(f"{self.base_url}/chitietblockchain")
            
            if response.status_code == 200:
                self.log_result("Blockchain Access", True, "Blockchain detail page accessible")
                
                # Test API endpoint nếu có
                # Hoặc kiểm tra qua database/file system
                # Ở đây ta sẽ kiểm tra cơ bản
                
                if "Genesis Block" in response.text:
                    self.log_result("Genesis Block", True, "Genesis block exists")
                else:
                    self.log_result("Genesis Block", False, "Genesis block not found")
                
                if "Block #" in response.text:
                    self.log_result("Transaction Blocks", True, "Transaction blocks exist")
                    return True
                else:
                    self.log_result("Transaction Blocks", False, "No transaction blocks")
                    return False
            else:
                self.log_result("Blockchain Access", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Blockchain Integrity", False, f"Error: {str(e)}")
            return False
    
    def test_transaction_history(self):
        """Test 8: Kiểm tra lịch sử giao dịch"""
        try:
            response = self.session.get(f"{self.base_url}/view_transactions")
            
            if response.status_code == 200:
                self.log_result("Transaction History Access", True, "Page accessible")
                
                # Kiểm tra có transaction nào được hiển thị không
                if "ID Nhân Viên" in response.text or "employee_id" in response.text:
                    self.log_result("Transaction Display", True, "Transactions are displayed")
                    return True
                else:
                    self.log_result("Transaction Display", False, "No transactions displayed")
                    return False
            else:
                self.log_result("Transaction History", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Transaction History", False, f"Error: {str(e)}")
            return False
    
    def test_user_management(self):
        """Test 9: Kiểm tra quản lý người dùng (Admin only)"""
        try:
            response = self.session.get(f"{self.base_url}/user_management")
            
            if response.status_code == 200:
                self.log_result("User Management Access", True, "Admin can access user management")
                
                # Test tạo user mới
                new_user_data = {
                    'username': 'testuser_auto',
                    'password': 'testpass123',
                    'role': 'user'
                }
                
                create_response = self.session.post(f"{self.base_url}/create_user", data=new_user_data)
                
                if create_response.status_code == 200:
                    result = create_response.json()
                    if result.get('success'):
                        self.log_result("Create User", True, "New user created successfully")
                        return True
                    else:
                        self.log_result("Create User", False, f"API error: {result}")
                        return False
                else:
                    self.log_result("Create User", False, f"HTTP {create_response.status_code}")
                    return False
            else:
                self.log_result("User Management Access", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Management", False, f"Error: {str(e)}")
            return False
    
    def test_reports_statistics(self):
        """Test 10: Kiểm tra báo cáo và thống kê"""
        try:
            response = self.session.get(f"{self.base_url}/reports")
            
            if response.status_code == 200:
                self.log_result("Reports Access", True, "Reports page accessible")
                
                # Kiểm tra có statistics không
                if "Tổng lương" in response.text or "total_salary" in response.text:
                    self.log_result("Statistics Display", True, "Statistics are shown")
                    
                    # Test export PDF
                    pdf_response = self.session.get(f"{self.base_url}/export/pdf")
                    if pdf_response.status_code == 200:
                        self.log_result("PDF Export", True, "PDF export works")
                    else:
                        self.log_result("PDF Export", False, f"PDF export failed: {pdf_response.status_code}")
                    
                    return True
                else:
                    self.log_result("Statistics Display", False, "No statistics shown")
                    return False
            else:
                self.log_result("Reports Access", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Reports/Statistics", False, f"Error: {str(e)}")
            return False
    
    def test_crypto_functionality(self):
        """Test 11: Kiểm tra tính năng mã hóa"""
        try:
            # Kiểm tra file crypto_keys.json có tồn tại
            if os.path.exists('crypto_keys.json'):
                self.log_result("Crypto Keys", True, "Crypto keys file exists")
                
                # Đọc và validate keys
                with open('crypto_keys.json', 'r') as f:
                    keys = json.load(f)
                
                required_keys = ['aes_key', 'iv', 'rsa_private_key']
                missing_keys = [key for key in required_keys if key not in keys]
                
                if not missing_keys:
                    self.log_result("Crypto Keys Validation", True, "All crypto keys present")
                    return True
                else:
                    self.log_result("Crypto Keys Validation", False, f"Missing keys: {missing_keys}")
                    return False
            else:
                self.log_result("Crypto Keys", False, "crypto_keys.json not found")
                return False
                
        except Exception as e:
            self.log_result("Crypto Functionality", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Chạy tất cả các test"""
        print("🚀 STARTING COMPREHENSIVE PAYROLL SYSTEM TESTS")
        print("=" * 60)
        
        # Danh sách các test theo thứ tự
        tests = [
            ("Server Status", self.test_server_running),
            ("Database Setup", self.test_database_setup),
            ("Authentication", self.test_authentication),
            ("Employee Management", self.test_employee_management),
            ("Attendance/KPI Input", self.test_attendance_kpi_input),
            ("Payroll Processing", self.test_payroll_processing),
            ("Blockchain Integrity", self.test_blockchain_integrity),
            ("Transaction History", self.test_transaction_history),
            ("User Management", self.test_user_management),
            ("Reports/Statistics", self.test_reports_statistics),
            ("Crypto Functionality", self.test_crypto_functionality)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_result(test_name, False, f"Unexpected error: {str(e)}")
        
        # Tổng kết
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! System is working great!")
        elif success_rate >= 70:
            print("✨ GOOD! Most features are working, minor issues to fix")
        elif success_rate >= 50:
            print("⚠️  MODERATE! Several issues need attention")
        else:
            print("🚨 POOR! Major issues found, system needs significant fixes")
        
        # Chi tiết kết quả
        print("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] else "❌"
            print(f"{status_icon} {test_name}: {result['message']}")
        
        return success_rate >= 70

def main():
    """Hàm main để chạy test suite"""
    print("🔧 Payroll Blockchain System - Automated Test Suite")
    print("Make sure your Flask server is running on http://localhost:5000")
    
    response = input("\nPress Enter to start testing (or 'q' to quit): ")
    if response.lower() == 'q':
        return
    
    tester = PayrollSystemTester()
    success = tester.run_all_tests()
    
    # Lưu kết quả vào file
    with open(f'test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Test results saved to test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    if not success:
        print("\n🔧 TROUBLESHOOTING TIPS:")
        print("1. Make sure Flask server is running: python app.py")
        print("2. Check if all dependencies are installed: pip install -r requirements.txt")
        print("3. Verify database permissions and file locations")
        print("4. Check browser console for JavaScript errors")
        print("5. Review detailed error messages above")

if __name__ == "__main__":
    main()