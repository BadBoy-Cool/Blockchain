#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Benchmark Test cho Blockchain và Crypto Utils
Đo lường hiệu suất của các thuật toán mã hóa và blockchain
"""

import time
import json
import os
import statistics
from datetime import datetime
import base64

# Import các class từ file gốc
from blockchain import Blockchain, SalaryData, Transaction
from crypto_utils import CryptoUtils

def create_sample_salary_data(size="medium"):
    """Tạo dữ liệu lương mẫu với kích thước khác nhau"""
    if size == "small":
        return SalaryData("Nguyen Van A", 15000000, 1500000, 2000000)
    elif size == "medium":
        return SalaryData("Tran Thi B", 25000000, 2500000, 3500000)
    else:  # large
        return SalaryData("Le Van C" * 10, 50000000, 5000000, 7500000)

def benchmark_aes_encryption(crypto, test_runs=100):
    """Đo hiệu suất mã hóa AES-256"""
    print("🔒 Đang test hiệu suất AES-256...")
    
    # Tạo dữ liệu test với kích thước khác nhau
    test_data = [
        ("Small (0.1KB)", json.dumps(create_sample_salary_data("small").to_dict())),
        ("Medium (1KB)", json.dumps(create_sample_salary_data("medium").to_dict()) * 10),
        ("Large (5KB)", json.dumps(create_sample_salary_data("large").to_dict()) * 50)
    ]
    
    results = []
    
    for data_type, data in test_data:
        data_size = len(data.encode('utf-8'))
        
        # Test mã hóa
        encrypt_times = []
        decrypt_times = []
        
        for _ in range(test_runs):
            # Đo thời gian mã hóa
            start_time = time.perf_counter()
            encrypted = crypto.aes_encrypt(data)
            encrypt_time = time.perf_counter() - start_time
            encrypt_times.append(encrypt_time)
            
            # Đo thời gian giải mã
            start_time = time.perf_counter()
            decrypted = crypto.aes_decrypt(encrypted)
            decrypt_time = time.perf_counter() - start_time
            decrypt_times.append(decrypt_time)
            
            # Verify integrity
            assert decrypted == data, "Dữ liệu sau giải mã không khớp!"
        
        results.append({
            'type': data_type,
            'size_bytes': data_size,
            'avg_encrypt_time': statistics.mean(encrypt_times),
            'avg_decrypt_time': statistics.mean(decrypt_times),
            'std_encrypt_time': statistics.stdev(encrypt_times) if len(encrypt_times) > 1 else 0,
            'std_decrypt_time': statistics.stdev(decrypt_times) if len(decrypt_times) > 1 else 0
        })
        
        print(f"✅ {data_type}: Encrypt {statistics.mean(encrypt_times):.6f}s, Decrypt {statistics.mean(decrypt_times):.6f}s")
    
    return results

def benchmark_rsa_signing(crypto, test_runs=50):
    """Đo hiệu suất ký số RSA"""
    print("🔐 Đang test hiệu suất RSA signing...")
    
    test_messages = [
        ("Small message", "user123"),
        ("Medium message", "user456_with_longer_name"),
        ("Large message", "very_long_username_for_testing_performance" * 5)
    ]
    
    results = []
    
    for msg_type, username in test_messages:
        sign_times = []
        
        for _ in range(test_runs):
            # Đo thời gian ký
            start_time = time.perf_counter()
            timestamp, signature = crypto.sign_login_message(username)
            sign_time = time.perf_counter() - start_time
            sign_times.append(sign_time)
        
        results.append({
            'type': msg_type,
            'message_length': len(username),
            'avg_sign_time': statistics.mean(sign_times),
            'std_sign_time': statistics.stdev(sign_times) if len(sign_times) > 1 else 0
        })
        
        print(f"✅ {msg_type}: Sign {statistics.mean(sign_times):.6f}s")
    
    return results

def benchmark_blockchain_operations(test_runs=10):
    """Đo hiệu suất các thao tác blockchain"""
    print("⛓️  Đang test hiệu suất Blockchain...")
    
    difficulties = [1, 2, 3, 4]
    results = []
    
    for difficulty in difficulties:
        print(f"📊 Testing với độ khó: {difficulty}")
        
        # Tạo blockchain mới cho mỗi test
        test_file = f"test_blockchain_diff_{difficulty}.json"
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Tạo blockchain với độ khó cụ thể
        blockchain = Blockchain(difficulty=difficulty)
        blockchain.blockchain_file = test_file
        
        # Tạo transactions mẫu
        crypto = CryptoUtils()
        transactions = []
        for i in range(5):  # 5 transactions per block
            salary_data = create_sample_salary_data()
            tx_data = json.dumps({
                'employee_name': salary_data.name,
                'basic_salary': salary_data.amount,
                'discount': salary_data.discount,
                'bonus': salary_data.bonus,
                'total_salary': salary_data.amount - salary_data.discount + salary_data.bonus,
                'timestamp': time.time(),
                'processed_by': f'admin_{i}'
            })
            
            # Mã hóa transaction
            encrypted_tx = crypto.aes_encrypt(tx_data)
            encoded_tx = base64.b64encode(encrypted_tx).decode()
            transactions.append(encoded_tx)
        
        # Đo thời gian tạo block
        create_times = []
        validate_times = []
        
        for run in range(test_runs):
            # Đo thời gian tạo block
            start_time = time.perf_counter()
            try:
                new_block = blockchain.add_block(transactions.copy())
                create_time = time.perf_counter() - start_time
                create_times.append(create_time)
                
                # Đo thời gian validate chain
                start_time = time.perf_counter()
                is_valid = blockchain.validate_chain()
                validate_time = time.perf_counter() - start_time
                validate_times.append(validate_time)
                
                print(f"  Run {run+1}/{test_runs}: Create {create_time:.3f}s, Validate {validate_time:.6f}s")
                
            except Exception as e:
                print(f"  ❌ Lỗi trong run {run+1}: {e}")
                continue
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        backup_file = test_file.replace('.json', '_backup.json')
        if os.path.exists(backup_file):
            os.remove(backup_file)
        
        if create_times and validate_times:
            results.append({
                'difficulty': difficulty,
                'avg_create_time': statistics.mean(create_times),
                'avg_validate_time': statistics.mean(validate_times),
                'std_create_time': statistics.stdev(create_times) if len(create_times) > 1 else 0,
                'std_validate_time': statistics.stdev(validate_times) if len(validate_times) > 1 else 0,
                'total_blocks_created': len(create_times)
            })
    
    return results

def print_comparison_tables(aes_results, rsa_results, blockchain_results):
    """In các bảng so sánh kết quả"""
    print("\n" + "="*80)
    print("📊 BẢNG SO SÁNH HIỆU SUẤT")
    print("="*80)
    
    # Bảng 3: So sánh thuật toán mã hóa
    print("\n🔒 BẢNG 3: So sánh hiệu suất thuật toán mã hóa")
    print("-" * 80)
    print(f"{'Thuật toán':<12} | {'Dữ liệu':<12} | {'Mã hóa (ms)':<12} | {'Giải mã (ms)':<12} | {'Nhận xét'}")
    print("-" * 80)
    
    for result in aes_results:
        if "Medium" in result['type']:  # Chỉ hiển thị kết quả medium cho so sánh
            encrypt_ms = result['avg_encrypt_time'] * 1000
            decrypt_ms = result['avg_decrypt_time'] * 1000
            print(f"{'AES-256':<12} | {'1KB':<12} | {encrypt_ms:<12.3f} | {decrypt_ms:<12.3f} | Nhanh, phù hợp mã hóa giao dịch")
    
    # Giả lập RSA cho so sánh (RSA thường chậm hơn nhiều)
    for result in rsa_results:
        if "Medium" in result['type']:
            sign_ms = result['avg_sign_time'] * 1000
            print(f"{'RSA-2048':<12} | {'Sign only':<12} | {sign_ms:<12.3f} | {'N/A':<12} | Chậm hơn, phù hợp ký số")
    
    # Bảng 4: So sánh hiệu suất blockchain
    print(f"\n⛓️  BẢNG 4: So sánh hiệu suất blockchain")
    print("-" * 80)
    print(f"{'Độ khó':<8} | {'Tạo block (s)':<15} | {'Validate (ms)':<15} | {'Nhận xét'}")
    print("-" * 80)
    
    for result in blockchain_results:
        create_s = result['avg_create_time']
        validate_ms = result['avg_validate_time'] * 1000
        
        if result['difficulty'] == 1:
            comment = "Nhanh, phù hợp hệ thống nhỏ"
        elif result['difficulty'] == 2:
            comment = "Cân bằng bảo mật và tốc độ"
        elif result['difficulty'] == 3:
            comment = "Bảo mật cao, chi phí tính toán lớn"
        else:
            comment = "Rất bảo mật, chi phí rất cao"
        
        print(f"{result['difficulty']:<8} | {create_s:<15.3f} | {validate_ms:<15.3f} | {comment}")

def generate_detailed_report(aes_results, rsa_results, blockchain_results):
    """Tạo báo cáo chi tiết"""
    report = {
        'test_timestamp': datetime.now().isoformat(),
        'aes_encryption': aes_results,
        'rsa_signing': rsa_results,
        'blockchain_operations': blockchain_results,
        'analysis': {
            'aes_vs_rsa_speed_ratio': None,
            'blockchain_difficulty_impact': None,
            'recommendations': []
        }
    }
    
    # Phân tích tốc độ AES vs RSA
    aes_medium = next((r for r in aes_results if "Medium" in r['type']), None)
    rsa_medium = next((r for r in rsa_results if "Medium" in r['type']), None)
    
    if aes_medium and rsa_medium:
        speed_ratio = rsa_medium['avg_sign_time'] / aes_medium['avg_encrypt_time']
        report['analysis']['aes_vs_rsa_speed_ratio'] = speed_ratio
        report['analysis']['recommendations'].append(
            f"AES-256 nhanh hơn RSA {speed_ratio:.1f} lần trong xử lý giao dịch, "
            "nên sử dụng AES để mã hóa dữ liệu lương và RSA để xác thực."
        )
    
    # Phân tích tác động độ khó blockchain
    if len(blockchain_results) >= 2:
        diff_1 = next((r for r in blockchain_results if r['difficulty'] == 1), None)
        diff_3 = next((r for r in blockchain_results if r['difficulty'] == 3), None)
        
        if diff_1 and diff_3:
            impact_ratio = diff_3['avg_create_time'] / diff_1['avg_create_time']
            report['analysis']['blockchain_difficulty_impact'] = impact_ratio
            report['analysis']['recommendations'].append(
                f"Tăng độ khó từ 1 lên 3 làm thời gian tạo block tăng {impact_ratio:.1f} lần, "
                "cần cân bằng giữa bảo mật và hiệu suất."
            )
    
    # Lưu báo cáo
    with open('performance_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Báo cáo chi tiết đã được lưu vào: performance_report.json")
    return report

def main():
    """Chạy tất cả các test benchmark"""
    print("🚀 BẮT ĐẦU BENCHMARK TEST")
    print("=" * 50)
    
    try:
        # Khởi tạo crypto utils
        crypto = CryptoUtils()
        print("✅ CryptoUtils đã được khởi tạo")
        
        # Test AES encryption
        aes_results = benchmark_aes_encryption(crypto, test_runs=50)
        
        # Test RSA signing  
        rsa_results = benchmark_rsa_signing(crypto, test_runs=30)
        
        # Test blockchain operations
        blockchain_results = benchmark_blockchain_operations(test_runs=5)
        
        # In bảng so sánh
        print_comparison_tables(aes_results, rsa_results, blockchain_results)
        
        # Tạo báo cáo chi tiết
        report = generate_detailed_report(aes_results, rsa_results, blockchain_results)
        
        print(f"\n🎉 HOÀN THÀNH BENCHMARK!")
        print("📊 Kết quả có thể sử dụng cho bảng 3 và 4 trong báo cáo của bạn")
        
    except Exception as e:
        print(f"❌ Lỗi trong quá trình benchmark: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()