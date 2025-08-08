import traceback
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import json
import sqlite3
import base64
import datetime
from datetime import datetime
from backend.crypto_utils import verify_signature
import atexit
from contextlib import contextmanager
import io
import os
import time
import subprocess

# Import backend modules
from backend.database import init_db
from backend.payroll_system import PayrollSystem
#from generate_keys import Wallet
from backend.crypto_utils import CryptoUtils
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

app = Flask(__name__)
app.secret_key = '123'

# Khởi tạo CSDL
init_db()

# Biến global để đảm bảo chỉ có một instance PayrollSystem
_payroll_system = None
_system_lock = False
# Tạo một instance duy nhất của PayrollSystem để dùng chung
payroll_system = PayrollSystem()

# Tạo class AuthSystem đơn giản
class AuthSystem:
    def __init__(self):
        self.init_auth_db()
    
    def init_auth_db(self):
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY,
                      username TEXT UNIQUE,
                      password TEXT,
                      role TEXT DEFAULT 'user',
                      last_login TIMESTAMP,
                      is_active BOOLEAN DEFAULT 1)''')
        
        # Tạo tài khoản admin mặc định
        public_key = CryptoUtils.generate_rsa_key_pair(save_to=f"user_admin_keys.json")['public_key']

        c.execute("INSERT OR IGNORE INTO users (username, public_key, role) VALUES (?, ?, ?)",
                ("admin", public_key, "admin"))
        
        conn.commit()
        conn.close()
    
    def verify_user(self, username, timestamp, signature):
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()

        c.execute("SELECT id, username, role, public_key, employee_id, is_active FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()

        if row and row[5] == 1:  # kiểm tra active
            db_public_key = row[3]
            message = f"{timestamp}:{username}"  # ✅ Sửa chỗ này

            if verify_signature(db_public_key, message, signature):
                return {
                    'id': row[0],
                    'username': row[1],
                    'role': row[2],
                    'employee_id': row[3]
                }

        return None

        

    def verify_signature(public_key_pem, message, signature_b64):
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())
            public_key.verify(
                base64.b64decode(signature_b64),
                message.encode(),
                padding.PSS(  # ✅ KHỚP VỚI sign_message.py
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print("⛔ Signature verification failed:", e)
            return False

      
                   
    def get_all_users(self):
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute("SELECT id, username, role, password, last_login, is_active FROM users")
        users = c.fetchall()
        conn.close()
        return users

# Tạo class ReportGenerator đơn giản
class ReportGenerator:
    def generate_salary_report_pdf(self):
        # Tạo PDF đơn giản (mock)
        content = "Salary Report - Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        buffer = io.BytesIO()
        buffer.write(content.encode())
        buffer.seek(0)
        return buffer

# Khởi tạo các instance
auth_system = AuthSystem()
report_gen = ReportGenerator()

# Decorator functions
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Bạn không có quyền truy cập trang này', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def get_payroll_system():
    """Singleton pattern cho PayrollSystem"""
    global _payroll_system, _system_lock
    
    if _payroll_system is None and not _system_lock:
        _system_lock = True
        try:
            print("Initializing PayrollSystem...")
            _payroll_system = PayrollSystem()
            
            # Đảm bảo lưu blockchain khi thoát ứng dụng
            atexit.register(save_blockchain_on_exit)
            
            print("PayrollSystem initialized successfully")
        except Exception as e:
            print(f"Error initializing PayrollSystem: {e}")
            _system_lock = False
            raise
        finally:
            _system_lock = False
    
    return _payroll_system

def save_blockchain_on_exit():
    """Lưu blockchain khi thoát ứng dụng"""
    global _payroll_system
    if _payroll_system:
        try:
            _payroll_system.blockchain.save_to_file()
            _payroll_system.blockchain.backup_chain()
            print("Blockchain saved on exit")
        except Exception as e:
            print(f"Error saving blockchain on exit: {e}")

@contextmanager
def payroll_transaction():
    """Context manager để đảm bảo transaction safety"""
    payroll = get_payroll_system()
    try:
        yield payroll
        # Lưu sau mỗi transaction thành công
        payroll.blockchain.save_to_file()
    except Exception as e:
        print(f"Transaction error: {e}")
        raise
    
# Routes
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Cập nhật route /login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        timestamp = request.form['timestamp'] 
        signature = request.form['signature']

        auth_system = AuthSystem()
        user = auth_system.verify_user(username, timestamp, signature)

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['employee_id'] = user['employee_id']
            print("[DEBUG] Đăng nhập:", session) 
            flash('Đăng nhập thành công!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('index'))
            else:
                return redirect(url_for('view_transactions'))

        flash('Đăng nhập thất bại. Vui lòng kiểm tra tên đăng nhập hoặc chữ ký.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/api/sign', methods=['POST'])
def api_sign():
    uploaded_file = request.files.get('jsonFile')
    username = request.form.get('username')

    if not uploaded_file or not username:
        return jsonify({'error': 'Thiếu file hoặc username'}), 400

    try:
        keys = json.load(uploaded_file)
        private_pem = keys.get('private_key')

        if not private_pem:
            return jsonify({'error': 'Không tìm thấy private_key trong JSON'}), 400

        private_key = serialization.load_pem_private_key(
            private_pem.encode(),
            password=None,
        )

        timestamp = int(time.time())
        message = f"{timestamp}:{username}".encode()

        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        signature_b64 = base64.b64encode(signature).decode()

        return jsonify({
            'username': username,
            'timestamp': timestamp,
            'signature': signature_b64
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/run_script', methods=['POST'])
def run_script():
    try:
        # Cách khác: dùng os.system (không lấy được output, chỉ trả về exit code)
        exit_code = os.system('login.bat')
        if exit_code != 0:
            return jsonify({'success': False, 'error': f'Exit code: {exit_code}'}), 500

        # Nếu cần lấy output, dùng subprocess như trước là tốt nhất
        return jsonify({'success': True, 'output': f'Batch file executed, exit code: {exit_code}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất thành công', 'success')
    return redirect(url_for('login'))

@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        agreed_salary = float(request.form['salary'])
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        from backend.crypto_utils import CryptoUtils
        crypto = CryptoUtils()
        public_key = crypto.get_public_key()
        c.execute("INSERT INTO employees (name, agreed_salary, public_key) VALUES (?, ?, ?)",
                  (name, agreed_salary, public_key))
        conn.commit()
        employee_id = c.lastrowid
        conn.close()
        return jsonify({'status': 'success', 'employee_id': employee_id})
    return render_template('add_employee.html')

@app.route('/add_data', methods=['GET', 'POST'])
@login_required
def add_data():
    if request.method == 'POST':
        employee_id = int(request.form['employee_id'])
        date = request.form['date']
        hours_worked = float(request.form['hours_worked'])
        overtime_hours = float(request.form['overtime_hours'])
        kpi_score = float(request.form['kpi_score'])
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute("INSERT INTO attendance (employee_id, date, hours_worked, overtime_hours) VALUES (?, ?, ?, ?)",
                  (employee_id, date, hours_worked, overtime_hours))
        c.execute("INSERT INTO kpi (employee_id, date, kpi_score) VALUES (?, ?, ?)",
                  (employee_id, date, kpi_score))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success'})
    
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM employees")
    employees = c.fetchall()
    conn.close()
    return render_template('add_data.html', employees=employees)

# Route cải thiện cho process_payroll
@app.route('/process_payroll', methods=['GET', 'POST'])
@login_required
def process_payroll():
    if request.method == 'POST':
        try:
            employee_id = int(request.form['employee_id'])
            month = request.form['month']

            with payroll_transaction() as payroll:
                transaction = payroll.process_payroll(employee_id, month)

                # Lưu blockchain ra file (block đã được tạo bên trong process_payroll)
                payroll.blockchain.save_to_file()

                return app.response_class(
                    response=json.dumps({
                        'status': 'success', 
                        'transaction': transaction,
                        'blockchain_info': {
                            'total_blocks': len(payroll.blockchain.chain),
                            'last_block_hash': payroll.blockchain.get_latest_block().hash
                        }
                    }),
                    status=200,
                    mimetype='application/json'
                )

        except Exception as e:
            print("Error in process_payroll:", e)
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error', 
                'message': str(e),
                'details': 'Check server logs for more information'
            }), 500

    # GET method: hiển thị form
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()   
    c.execute("SELECT id, name FROM employees")
    employees = c.fetchall()
    conn.close()
    return render_template('process_payroll.html', employees=employees)



# Route cải thiện cho view_transactions
@app.route('/view_transactions')
@login_required
def view_transactions():
    try:
        payroll = get_payroll_system()
        transactions, errors = payroll.get_all_transactions()

        # Lấy thông tin từ session
        role = session.get('role')
        employee_id = session.get('employee_id')

        if role != 'admin':
            if 'employee_id' not in session:
                return render_template('view_transactions.html', transactions=[{
                    'error': f'❌ Session không có employee_id cho người dùng {session.get("username", "Không rõ")}',
                    'raw_data': str(session)
                }])
            if not employee_id:
                return render_template('view_transactions.html', transactions=[{
                    'error': f'❌ Tài khoản nhân viên {session.get("username", "Không rõ")} không có employee_id hợp lệ.',
                    'raw_data': str(session)
                }])
            transactions = [tx for tx in transactions if str(tx.get('employee_id')) == str(employee_id)]

        # Format các transaction
        formatted_transactions = []
        for tx in transactions:
            try:
                formatted_tx = {
                    'employee_id': tx.get('employee_id', 'N/A'),
                    'employee_name': tx.get('employee_name', 'N/A'),
                    'month': tx.get('month', 'N/A'),
                    'base_salary': tx.get('base_salary', 0),
                    'overtime_salary': tx.get('overtime_salary', 0),
                    'kpi_bonus': tx.get('kpi_bonus', 0),
                    'total_salary': tx.get('total_salary', 0),
                    'timestamp': tx.get('timestamp', 0),
                    'processed_date': tx.get('processed_date', 'N/A'),
                    'signature': tx.get('signature', '')[:50] + '...' if tx.get('signature') else 'N/A',
                    'block_index': tx.get('block_index', 'N/A'),
                    'block_hash': tx.get('block_hash', '')[:20] + '...' if tx.get('block_hash') else 'N/A'
                }
                formatted_transactions.append(formatted_tx)
            except Exception as e:
                formatted_transactions.append({
                    'error': f'Lỗi định dạng giao dịch: {str(e)}',
                    'raw_data': str(tx)[:100] + '...' if len(str(tx)) > 100 else str(tx)
                })

        # Chỉ admin mới xem được các lỗi
        if role == 'admin':
            for error in errors:
                formatted_transactions.append({
                    'error': f"Lỗi trong block {error.get('block_index', 'N/A')}: {error.get('error', 'Không xác định')}",
                    'raw_data': error.get('raw_data', 'Không có')
                })

        return render_template('view_transactions.html', transactions=formatted_transactions)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('view_transactions.html', transactions=[
            {'error': f'Lỗi hệ thống: {str(e)}', 'raw_data': ''}
        ])


# Tỉ giá đơn giản (bạn có thể lấy từ API sau nếu muốn)
currency_rates = {
    'USD': 1.0,
    'VND': 24000.0,
    'EUR': 0.85,
    'JPY': 110.0,
}

currency_symbols = {
    'USD': '$',
    'VND': '₫',
    'EUR': '€',
    'JPY': '¥',
}

def convert_currency(value, currency='USD'):
    rate = currency_rates.get(currency, 1.0)
    return value * rate


# Route cải thiện cho chitietblockchain
@app.route("/chitietblockchain")
@login_required
def chitietblockchain():
    payroll = get_payroll_system()
    blockchain = payroll.blockchain
    currency = request.args.get('currency', 'USD')

    # Ví dụ dữ liệu — bạn thay bằng dữ liệu thực tế của mình
    blockchain_stats = {
        'total_blocks': 5,
        'total_transactions': 20,
        'total_salary': 50000.0,
        'chain_integrity': '✅ Hợp lệ'
    }



    chain_valid = blockchain.validate_chain()  # kiểm tra lại sau restore

    blocks = []
    total_transactions = 0
    total_salary = 0

    for block in blockchain.chain:
        # có thể xử lý và format dữ liệu ở đây
        block_data = {
            "index": block.index,
            "transaction_count": len(block.transactions),
            "transactions": [],
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "is_valid": block.is_valid,
            "chain_valid": True,
            "size_bytes": len(json.dumps(block.to_dict()).encode("utf-8"))
        }

        if block.index > 0:
            prev_block = blockchain.chain[block.index - 1]
            if block.previous_hash != prev_block.hash:
                block_data["chain_valid"] = False

        for tx in block.transactions:
            try:
                tx_dict = blockchain._decode_transaction(tx)
                block_data["transactions"].append(tx_dict)

                # cộng lương để thống kê
                total_transactions += 1
                total_salary += tx_dict.get("total_salary", 0)

            except Exception as e:
                block_data["transactions"].append({
                    "error": str(e),
                    "raw_data": tx
                })

        blocks.append(block_data)

    blockchain_stats = {
        "total_blocks": len(blockchain.chain),
        "total_transactions": total_transactions,
        "total_salary": total_salary,
        "chain_integrity": "Hợp lệ" if chain_valid else "Không hợp lệ"
    }

    return render_template("chitietblockchain.html", blocks=blocks,currency=currency,currency_symbol=currency_symbols.get(currency, '$'),convert_currency=lambda x: convert_currency(x, currency),blockchain_stats=blockchain_stats, chain_valid=chain_valid)


# Route mới để kiểm tra trạng thái blockchain
@app.route('/blockchain_status')
@login_required
def blockchain_status():
    """API endpoint để kiểm tra trạng thái blockchain"""
    try:
        payroll = get_payroll_system()
        stats = payroll.get_system_stats()

        return jsonify({
            'status': 'success',
            'blockchain_info': stats['blockchain_info'],
            'blockchain_stats': stats['blockchain'],
            'total_transactions': stats['total_transactions'],
            'total_salary': stats['total_salary'],
            'decoding_errors': stats['decoding_errors']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Route backup/restore blockchain
@app.route('/backup_blockchain', methods=['POST'])
@admin_required
def backup_blockchain():
    """Tạo backup blockchain thủ công"""
    try:
        payroll = get_payroll_system()
        success = payroll.backup_blockchain()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Backup được tạo thành công'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Không thể tạo backup'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/restore_blockchain', methods=['POST'])
@login_required
def restore_blockchain():
    payroll = get_payroll_system()  # Lấy instance đã khởi tạo Blockchain
    if payroll.blockchain.restore_from_backup():
        flash("Đã khôi phục blockchain từ bản sao lưu", "success")
    else:
        flash("Khôi phục thất bại. Kiểm tra file backup.", "error")
    return redirect(url_for('chitietblockchain'))


# Force save blockchain (cho admin)
@app.route('/force_save_blockchain', methods=['POST'])
@admin_required
def force_save_blockchain():
    """Buộc lưu blockchain (dùng khi debug)"""
    try:
        payroll = get_payroll_system()
        payroll.blockchain.save_to_file()
        payroll.blockchain.backup_chain()
        
        return jsonify({
            'status': 'success',
            'message': 'Blockchain đã được lưu',
            'blocks': len(payroll.blockchain.chain)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
@app.route('/user_management')
@admin_required
def user_manager():
    conn = sqlite3.connect('payroll.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM employees")
    employees = c.fetchall()

    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    return render_template('user_management.html', users=users, employees=employees)

@app.route('/create_user', methods=['POST'])
@admin_required
def create_user():
    try:
        username = request.form['username']
        public_key = request.form['public_key']
        employee_id = request.form.get('employee_id') or None
        role = request.form.get('role', 'user')

        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, public_key, role, is_active, employee_id) VALUES (?, ?, ?, ?, ?)",
            (username, public_key, role, 1, employee_id)
        )
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/deactivate_user', methods=['POST'])
@admin_required
def deactivate_user():
    try:
        user_id = request.json['user_id']
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Thay thế phần route @app.route('/reports') trong app.py
@app.route('/reports')
@login_required
def reports():
    try:
        # Sử dụng ReportGenerator để lấy thống kê
        from backend.report_generator import ReportGenerator
        report_gen = ReportGenerator()
        stats = report_gen.get_salary_statistics()
        
        # Lấy thống kê từ blockchain
        blockchain_stats = payroll_system.blockchain.get_blockchain_stats()
        monthly_stats = payroll_system.blockchain.get_transaction_volume_by_month()
        
        # Cập nhật stats với thông tin blockchain
        stats.update({
            'blockchain_blocks': blockchain_stats.get('total_blocks', 0),
            'blockchain_valid': blockchain_stats.get('chain_valid', False)
        })
        
        print(f"Debug - Stats: {stats}")  # Debug line
        print(f"Debug - Monthly stats: {monthly_stats}")  # Debug line
        
        return render_template('reports.html', stats=stats, monthly_stats=monthly_stats)
        
    except Exception as e:
        print(f"[ERROR] Lỗi khi tạo báo cáo: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback với dữ liệu mặc định
        stats = {
            'total_salary': 0,
            'total_employees': 0,
            'total_transactions': 0,
            'avg_kpi': 0,
            'blockchain_blocks': 0,
            'blockchain_valid': False
        }
        monthly_stats = {}
        currency = 'USD'  # fallback về USD khi lỗi

    return render_template(
        'reports.html',
        stats=stats,
        monthly_stats=monthly_stats,
        currency=currency,
        currency_symbol=currency_symbols.get(currency, '$'),
        convert_currency=lambda x: convert_currency(x, currency)
    )
@app.route('/export/pdf')
@login_required
def export_pdf():
    try:
        from backend.report_generator import ReportGenerator
        report_gen = ReportGenerator()
        pdf_buffer = report_gen.generate_salary_report_pdf()
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=f'salary_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
            mimetype='text/plain'
        )
    except Exception as e:
        print(f'Error exporting PDF: {e}')
        flash(f'Lỗi xuất PDF: {str(e)}', 'error')
        return redirect(url_for('reports'))

@app.route('/export/excel')
@login_required
def export_excel():
    try:
        from backend.report_generator import ReportGenerator
        report_gen = ReportGenerator()
        excel_buffer = report_gen.generate_salary_report_excel()
        
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=f'salary_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        print(f'Error exporting Excel: {e}')
        flash(f'Lỗi xuất Excel: {str(e)}', 'error')
        return redirect(url_for('reports'))

# Jinja2 filter for JSON serialization
@app.template_filter('tojsonfilter')
def to_json_filter(obj):
    return json.dumps(obj)

# Thêm route debug vào app.py để kiểm tra dữ liệu

@app.route('/debug_blockchain')
@login_required
def debug_blockchain():
    """Route debug để kiểm tra dữ liệu blockchain"""
    try:
        debug_info = {
            'blockchain_blocks': len(payroll_system.blockchain.chain),
            'transactions_raw': [],
            'transactions_decoded': [],
            'decoding_errors': []
        }
        
        for i, block in enumerate(payroll_system.blockchain.chain):
            debug_info['transactions_raw'].append({
                'block_index': i,
                'transaction_count': len(block.transactions),
                'transactions': block.transactions[:2] if block.transactions else []  # First 2 for preview
            })
            
            for j, tx_b64 in enumerate(block.transactions):
                try:
                    if isinstance(tx_b64, str):
                        # Thử giải mã
                        encrypted_bytes = base64.b64decode(tx_b64)
                        decrypted_json = payroll_system.crypto.aes_decrypt(encrypted_bytes)
                        tx_dict = json.loads(decrypted_json)
                        
                        debug_info['transactions_decoded'].append({
                            'block_index': i,
                            'transaction_index': j,
                            'transaction': tx_dict
                        })
                    else:
                        # Nếu không phải string, có thể là dict
                        debug_info['transactions_decoded'].append({
                            'block_index': i,
                            'transaction_index': j,
                            'transaction': tx_b64,
                            'type': str(type(tx_b64))
                        })
                        
                except Exception as e:
                    debug_info['decoding_errors'].append({
                        'block_index': i,
                        'transaction_index': j,
                        'error': str(e),
                        'raw_data_preview': str(tx_b64)[:100] if tx_b64 else 'Empty'
                    })
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/debug_database')
@login_required
def debug_database():
    """Debug route để kiểm tra dữ liệu database"""
    try:
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        
        debug_info = {}
        
        # Kiểm tra bảng employees
        c.execute("SELECT COUNT(*) FROM employees")
        debug_info['employees_count'] = c.fetchone()[0]
        
        c.execute("SELECT * FROM employees LIMIT 5")
        debug_info['employees_sample'] = c.fetchall()
        
        # Kiểm tra bảng attendance
        c.execute("SELECT COUNT(*) FROM attendance")
        debug_info['attendance_count'] = c.fetchone()[0]
        
        c.execute("SELECT * FROM attendance LIMIT 5")
        debug_info['attendance_sample'] = c.fetchall()
        
        # Kiểm tra bảng kpi
        c.execute("SELECT COUNT(*) FROM kpi")
        debug_info['kpi_count'] = c.fetchone()[0]
        
        c.execute("SELECT * FROM kpi LIMIT 5")
        debug_info['kpi_sample'] = c.fetchall()
        
        # Kiểm tra tháng có dữ liệu
        c.execute("""SELECT strftime('%Y-%m', date) as month, COUNT(*) as count 
                     FROM kpi 
                     GROUP BY strftime('%Y-%m', date) 
                     ORDER BY month""")
        debug_info['months_with_data'] = c.fetchall()
        
        conn.close()
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()})

@app.route('/test_transaction')
@login_required  
def test_transaction():
    """Tạo một giao dịch test để kiểm tra"""
    try:
        # Kiểm tra xem có nhân viên nào không
        conn = sqlite3.connect('payroll.db')
        c = conn.cursor()
        c.execute("SELECT id FROM employees LIMIT 1")
        employee = c.fetchone()
        
        if not employee:
            # Tạo nhân viên test
            from backend.crypto_utils import CryptoUtils
            crypto = CryptoUtils()
            c.execute("INSERT INTO employees (name, agreed_salary, public_key) VALUES (?, ?, ?)",
                      ("Test Employee", 1000, crypto.get_public_key()))
            employee_id = c.lastrowid
            
            # Thêm dữ liệu attendance và kpi test
            c.execute("INSERT INTO attendance (employee_id, date, hours_worked, overtime_hours) VALUES (?, ?, ?, ?)",
                      (employee_id, '2025-07-01', 160, 10))
            c.execute("INSERT INTO kpi (employee_id, date, kpi_score) VALUES (?, ?, ?)",
                      (employee_id, '2025-07-01', 85))
            conn.commit()
        else:
            employee_id = employee[0]
            
        conn.close()
        
        # Tạo giao dịch test
        result = payroll_system.process_payroll(employee_id, '2025-07')
        
        return jsonify({
            'status': 'success',
            'message': 'Tạo giao dịch test thành công',
            'transaction': result,
            'employee_id': employee_id
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'traceback': traceback.format_exc()
        })

@app.route('/reset_blockchain')
@admin_required
def reset_blockchain():
    """Reset blockchain để test (chỉ admin)"""
    try:
        global payroll_system
        payroll_system = PayrollSystem()
        
        return jsonify({
            'status': 'success',
            'message': 'Đã reset blockchain thành công',
            'blocks': len(payroll_system.blockchain.chain)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)