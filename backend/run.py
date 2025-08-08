#!/usr/bin/env python3
"""
Script khởi động cho hệ thống quản lý lương blockchain
"""

import os
import sys

def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    required_packages = [
        'flask',
        'cryptography'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Thiếu các package sau:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n Cài đặt bằng lệnh:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_directories():
    """Tạo các thư mục cần thiết"""
    directories = [
        'backend',
        'static',
        'templates'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Đã tạo thư mục: {directory}")

def main():
    print(" Khởi động hệ thống quản lý lương blockchain...")
    
    # Kiểm tra dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Tạo thư mục
    create_directories()
    
    # Import và chạy app
    try:
        from app import app
        print("✅ Khởi tạo thành công!")
        print(" Truy cập: http://localhost:5000")
        print(" Tài khoản mặc định:")
        print("   - Username: admin")
        print("   - Password: admin123")
        print("\n Đang khởi động server...")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except ImportError as e:
        print(f"❌ Lỗi import: {e}")
        print(" Đảm bảo tất cả file đã được tạo đúng cấu trúc")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi khởi động: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()