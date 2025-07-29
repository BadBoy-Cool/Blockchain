#!/usr/bin/env python3
"""
Script test để kiểm tra và sửa lỗi mã hóa
"""

import sys
import os
sys.path.append('backend')

def test_crypto_utils():
    """Test CryptoUtils sau khi sửa lỗi"""
    print("=== TESTING CRYPTO UTILS ===")
    
    try:
        from backend.crypto_utils import CryptoUtils
        crypto = CryptoUtils()
        
        # Test 1: Mã hóa/giải mã cơ bản
        print("\n1. Testing basic encryption/decryption...")
        success = crypto.test_encryption()
        
        if not success:
            print("❌ Basic encryption test FAILED")
            return False
        
        # Test 2: Mã hóa dữ liệu JSON (giống như trong transaction)
        print("\n2. Testing JSON data encryption...")
        test_transaction = {
            'employee_id': 1,
            'employee_name': 'Nguyễn Văn A',
            'month': '2025-07',
            'total_salary': 1500.50
        }
        
        import json
        json_data = json.dumps(test_transaction, ensure_ascii=False)
        print(f"Original JSON: {json_data}")
        
        # Mã hóa
        encrypted = crypto.aes_encrypt(json_data)
        print(f"Encrypted length: {len(encrypted)} bytes")
        
        # Giải mã
        decrypted = crypto.aes_decrypt(encrypted)
        decrypted_dict = json.loads(decrypted)
        print(f"Decrypted JSON: {decrypted}")
        
        # Kiểm tra
        if test_transaction == decrypted_dict:
            print("✅ JSON encryption test PASSED")
        else:
            print("❌ JSON encryption test FAILED")
            return False
        
        # Test 3: Test với dữ liệu có ký tự đặc biệt
        print("\n3. Testing special characters...")
        special_data = "Dữ liệu có ký tự đặc biệt: áàảãạéèẻẽẹ 测试 🎉"
        encrypted_special = crypto.aes_encrypt(special_data)
        decrypted_special = crypto.aes_decrypt(encrypted_special)
        
        if special_data == decrypted_special:
            print("✅ Special characters test PASSED")
        else:
            print("❌ Special characters test FAILED")
            return False
        
        print("\n🎉 ALL TESTS PASSED! Crypto fix is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_payroll_processing():
    """Test xử lý payroll sau khi sửa lỗi"""
    print("\n=== TESTING PAYROLL PROCESSING ===")
    
    try:
        # Khởi tạo database và payroll system
        from backend.database import init_db
        from backend.payroll_system import PayrollSystem
        
        print("1. Initializing database and payroll system...")
        init_db()
        payroll = PayrollSystem()
        
        print("2. Testing payroll processing...")
        # Xử lý lương cho nhân viên ID 1, tháng 2025-07
        result = payroll.process_payroll(1, '2025-07')
        
        print(f"✅ Payroll processing successful!")
        print(f"Employee: {result.get('employee_name')}")
        print(f"Total salary: ${result.get('total_salary', 0):.2f}")
        print(f"Block count: {len(payroll.blockchain.chain)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Payroll test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Chạy tất cả các test"""
    print("🔧 FIXING BLOCKCHAIN PAYROLL ENCRYPTION ISSUE")
    print("=" * 50)
    
    # Test 1: Crypto utils
    crypto_ok = test_crypto_utils()
    
    if not crypto_ok:
        print("\n❌ Crypto tests failed. Please check the crypto_utils.py file.")
        return
    
    # Test 2: Payroll processing
    payroll_ok = test_payroll_processing()
    
    if crypto_ok and payroll_ok:
        print("\n🎉 ALL SYSTEMS WORKING! You can now use the payroll system.")
        print("\nNext steps:")
        print("1. Start the Flask app: python app.py")
        print("2. Go to /process_payroll and try adding salary data")
        print("3. Check /view_transactions to see if data is properly encrypted/decrypted")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main()