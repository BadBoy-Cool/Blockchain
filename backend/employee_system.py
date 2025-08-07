import sqlite3
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from backend.crypto_utils import CryptoUtils

class CountryManager:
    SUPPORTED_COUNTRIES = {
        'VN': {
            'name': 'Việt Nam', 'currency': 'VND', 'currency_symbol': '₫', 'cost_index': 0.4,
            'tax_rate': 0.10, 'social_insurance': 0.105, 'overtime_rate': 1.5, 'min_salary_usd': 200,
            'working_hours_per_month': 176, 'public_holidays': 10, 'valid_contracts': ['FULLTIME', 'PARTTIME', 'CONTRACT', 'INTERN'],
            'language': 'vi', 'timezone': 'Asia/Ho_Chi_Minh', 'compliance_notes': 'Phải tuân thủ Bộ luật Lao động Việt Nam 2019'
        },
        'US': {
            'name': 'United States', 'currency': 'USD', 'currency_symbol': '$', 'cost_index': 1.0,
            'tax_rate': 0.22, 'social_insurance': 0.15, 'overtime_rate': 1.5, 'min_salary_usd': 1500,
            'working_hours_per_month': 173, 'public_holidays': 10, 'valid_contracts': ['FULLTIME', 'PARTTIME', 'FREELANCE', 'CONTRACT'],
            'language': 'en', 'timezone': 'America/New_York', 'compliance_notes': 'Must comply with FLSA and state labor laws'
        },
    }

    @staticmethod
    def get_country_info(country_code: str) -> Optional[Dict]:
        return CountryManager.SUPPORTED_COUNTRIES.get(country_code.upper())

class EmployeeValidator:
    @staticmethod
    def validate_employee_data(name: str, salary: float, country: str, contract_type: str, email: str = None) -> List[str]:
        errors = []
        # 1. Validate tên
        if not name or len(name.strip()) < 2:
            errors.append("Tên phải có ít nhất 2 ký tự")

        # 2. Validate email
        if email and '@' not in email:
            errors.append("Email không hợp lệ")

        # 3. Validate quốc gia
        country_info = CountryManager.get_country_info(country)
        if not country_info:
            errors.append(f"Quốc gia {country} không được hỗ trợ")
            return errors

        # 4. Validate lương theo chuẩn quốc gia
        min_salary = country_info['min_salary_usd']
        if salary < min_salary:
            errors.append(f"Lương tối thiểu tại {country_info['name']}: ${min_salary}")

        # 5. Validate loại hợp đồng
        valid_contracts = country_info['valid_contracts']
        if contract_type not in valid_contracts:
            errors.append(f"Loại hợp đồng {contract_type} không hợp lệ cho quốc gia {country_info['name']}")

        return errors

class ImprovedEmployeeSystem:
    def __init__(self):
        self.db_path = 'payroll.db'
        self.logger = logging.getLogger(__name__)
        self.crypto = CryptoUtils()

    def generate_employee_code(self, country_code: str) -> str:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM employees WHERE country_code = ?", (country_code,))
        count = c.fetchone()[0] + 1
        conn.close()
        return f"{country_code}{datetime.now().strftime('%Y')}{count:03d}"

    def add_employee_v2(self, employee_data: Dict, created_by: int = None) -> Dict:
        errors = EmployeeValidator.validate_employee_data(
            employee_data['name'],
            employee_data['agreed_salary'],
            employee_data['country'],
            employee_data['contract_type'],
            employee_data.get('email')
        )
        
        # Kiểm tra email trùng lặp
        if employee_data.get('email'):
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM employees WHERE email = ?", (employee_data.get('email'),))
            if c.fetchone()[0] > 0:
                errors.append("Email đã tồn tại")
            conn.close()
        
        if errors:
            return {'success': False, 'errors': errors}

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            employee_code = self.generate_employee_code(employee_data['country'])
            public_key = self.crypto.get_public_key()

            c.execute('''INSERT INTO employees (
                employee_code, name, email, agreed_salary_usd, country_code, contract_type, 
                department, position, public_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                employee_code,
                employee_data['name'],
                employee_data.get('email'),
                employee_data['agreed_salary'],
                employee_data['country'].upper(),
                employee_data['contract_type'].upper(),
                employee_data.get('department'),
                employee_data.get('position'),
                public_key
            ))

            employee_id = c.lastrowid
            conn.commit()
            conn.close()
            return {
                'success': True,
                'employee': {
                    'id': employee_id,
                    'employee_code': employee_code,
                    'name': employee_data['name'],
                    'country': employee_data['country']
                },
                'message': 'Thêm nhân viên thành công'
            }
        except Exception as e:
            self.logger.error(f"Lỗi thêm nhân viên: {e}")
            return {'success': False, 'errors': [str(e)]}