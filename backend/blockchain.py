import hashlib
import json
import time
from datetime import datetime
import base64
import threading
import os
from ecdsa import SigningKey, VerifyingKey, SECP256k1

class SalaryData:
    def __init__(self, name, amount, discount, bonus):
        self.name = name
        self.amount = amount
        self.discount = discount
        self.bonus = bonus

    def to_dict(self):
        return {
            "name": self.name,
            "amount": self.amount,
            "discount": self.discount,
            "bonus": self.bonus
        }

    @staticmethod
    def from_dict(data):
        return SalaryData(
            name=data['name'],
            amount=data['amount'],
            discount=data['discount'],
            bonus=data['bonus']
        )
    
class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
        self.is_valid = True

    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty=1):
        target = "0" * difficulty
        start_time = time.time()
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
            
        mining_time = time.time() - start_time
        print(f"Block mined: {self.hash} (Nonce: {self.nonce}, Time: {mining_time:.2f}s)")

    def get_size_bytes(self):
        return len(json.dumps(self.__dict__).encode())

    def validate_block(self):
        calculated_hash = self.calculate_hash()
        return calculated_hash == self.hash

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,  # Giữ nguyên format để lưu
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "nonce": self.nonce
        }

    @staticmethod
    def from_dict(data):
        # Tạo block từ dict, không cần decode transactions ở đây
        block = Block(
            index=data['index'],
            transactions=data['transactions'],  # Giữ nguyên format
            timestamp=data['timestamp'],
            previous_hash=data['previous_hash'],
            nonce=data.get('nonce', 0)
        )
        block.hash = data['hash']
        return block
    
class Blockchain:
    def __init__(self, difficulty=1):
        self.difficulty = difficulty
        self.chain = []
        self.pending_transactions = []
        self.mining_reward = 10
        self.blockchain_file = "blockchain.json"
        self.backup_file = "blockchain_backup.json"
        self.lock = threading.Lock()  # Thêm lock để đồng bộ
        
        if not self.load_existing_blockchain():
            print("Blockchain không thể load. Vui lòng kiểm tra file hoặc khôi phục từ backup.")

            #Tạo genesis block nếu chuỗi bị rỗng
        if len(self.chain) == 0:
            self.create_genesis_block()

    def load_existing_blockchain(self):
        try:
            if os.path.exists(self.blockchain_file):
                print(f"Loading existing blockchain from {self.blockchain_file}")
                with open(self.blockchain_file, 'r') as f:
                    data = json.load(f)
                    if data:
                        self.chain = [Block.from_dict(block_data) for block_data in data]
                        print(f"Loaded {len(self.chain)} blocks from existing blockchain")

                        if self.validate_chain():
                            print("Blockchain validation successful")
                            return True
                        else:
                            print("Blockchain validation failed. Không ghi đè.")
                            return False  # Không tạo genesis mới!
            return False
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            return False

    def create_genesis_block(self):
        """Tạo genesis block chỉ khi chưa có blockchain"""
        print("Creating new genesis block")
        genesis = Block(0, [], time.time(), "0")
        genesis.mine_block(self.difficulty)
        self.chain.append(genesis)
        self.save_to_file()
        self.backup_chain()
        return genesis

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
        with self.lock:  # Đảm bảo chỉ 1 thread thực hiện tại 1 thời điểm
            print(f"Adding block with {len(transactions)} transactions")
        """Thêm block mới và lưu ngay lập tức"""
        new_block = Block(
            len(self.chain), 
            transactions, 
            time.time(), 
            self.get_latest_block().hash
        )
        new_block.mine_block(self.difficulty)
        
        if self.validate_new_block(new_block):
            self.chain.append(new_block)
            self.pending_transactions = []
            
            # Lưu ngay sau khi thêm block
            self.save_to_file()
            self.backup_chain()
            
            print(f"Block #{new_block.index} added and saved to blockchain")
            return new_block
        else:
            raise Exception("Block không hợp lệ!")

    def save_to_file(self):
        """Lưu blockchain vào file JSON"""
        try:
            data = [block.to_dict() for block in self.chain]
            
            # Lưu vào file tạm trước
            temp_file = self.blockchain_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Rename file tạm thành file chính (atomic operation)
            os.replace(temp_file, self.blockchain_file)
            print(f"Blockchain saved to {self.blockchain_file}")
            
        except Exception as e:
            print(f"Error saving blockchain: {e}")

    def backup_chain(self):
        """Tạo backup của blockchain"""
        try:
            data = [block.to_dict() for block in self.chain]
            with open(self.backup_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Blockchain backup created: {self.backup_file}")
        except Exception as e:
            print(f"Error creating backup: {e}")

    def restore_from_backup(self):
        if os.path.exists(self.backup_file):
            with open(self.backup_file, 'r') as f:
                data = json.load(f)
                self.chain = [Block.from_dict(block) for block in data]
            self.save_to_file()
            return True
        return False
   

    def validate_new_block(self, new_block):
        latest_block = self.get_latest_block()
        
        if new_block.index != latest_block.index + 1:
            return False
            
        if new_block.previous_hash != latest_block.hash:
            return False
            
        if not new_block.validate_block():
            return False
            
        return True

    def validate_chain(self):
        """Validate toàn bộ blockchain"""
        try:
            if not self.chain[0].validate_block():
                print("Genesis block is invalid")
                return False

            for i in range(1, len(self.chain)):
                current_block = self.chain[i]
                previous_block = self.chain[i - 1]

                if not current_block.validate_block():
                    print(f"Block {i} has invalid hash")
                    return False

                if current_block.previous_hash != previous_block.hash:
                    print(f"Block {i} has invalid previous hash: {current_block.previous_hash} != {previous_block.hash}")
                    return False

            return True
        except Exception as e:
            print(f"Error validating chain: {e}")
            return False


    def add_transaction(self, transaction):
        """Thêm transaction vào pending list"""
        self.pending_transactions.append(transaction)

    def get_blockchain_stats(self):
        total_blocks = len(self.chain)
        total_transactions = sum(len(block.transactions) for block in self.chain)
        total_size = sum(block.get_size_bytes() for block in self.chain)
        
        return {
            'total_blocks': total_blocks,
            'total_transactions': total_transactions,
            'total_size_bytes': total_size,
            'chain_valid': self.validate_chain(),
            'difficulty': self.difficulty,
            'latest_block_hash': self.get_latest_block().hash if self.chain else "No blocks"
        }

    def get_blocks_with_details(self):
        blocks_info = []
        
        for i, block in enumerate(self.chain):
            block_info = {
                'index': block.index,
                'hash': block.hash,
                'previous_hash': block.previous_hash,
                'timestamp': block.timestamp,
                'timestamp_formatted': datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
                'nonce': block.nonce,
                'transaction_count': len(block.transactions),
                'transactions': block.transactions,
                'size_bytes': block.get_size_bytes(),
                'is_valid': block.validate_block(),
                'chain_valid': True if i == 0 else block.previous_hash == self.chain[i-1].hash
            }
            blocks_info.append(block_info)
            
        return blocks_info

    


    def get_transaction_volume_by_month(self):
        """Cải thiện hàm thống kê theo tháng"""
        monthly_stats = {}
        
        # Import crypto utils để decode
        try:
            from backend.crypto_utils import CryptoUtils
            crypto = CryptoUtils()
        except:
            crypto = None
        
        for block in self.chain:
            block_date = datetime.fromtimestamp(block.timestamp)
            month_key = block_date.strftime('%Y-%m')
            
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'transaction_count': 0,
                    'total_salary': 0,
                    'blocks': 0
                }
            
            monthly_stats[month_key]['blocks'] += 1
            
            # Decode và tính transactions
            for tx_data in block.transactions:
                try:
                    tx_dict = self._decode_transaction(tx_data, crypto)
                    
                    if tx_dict and isinstance(tx_dict, dict):
                        monthly_stats[month_key]['transaction_count'] += 1
                        
                        # Lấy total_salary
                        salary = tx_dict.get('total_salary', 0)
                        if isinstance(salary, (int, float)):
                            monthly_stats[month_key]['total_salary'] += salary
                        
                except Exception as e:
                    print(f"Error decoding transaction: {e}")
                    continue
                    
        return monthly_stats

# Thêm vào class Blockchain trong blockchain.py

    def _decode_transaction(self, tx_data, crypto=None):
        """Helper function để decode transaction với error handling tốt hơn"""
        try:
            if isinstance(tx_data, str):
                # Import crypto utils nếu chưa có
                if crypto is None:
                    try:
                        from backend.crypto_utils import CryptoUtils
                        crypto = CryptoUtils()
                    except:
                        return None
                
                # Thử decode base64 + decrypt
                try:
                    encrypted_bytes = base64.b64decode(tx_data)
                    decrypted_json = crypto.aes_decrypt(encrypted_bytes)
                    return json.loads(decrypted_json)
                except Exception as decode_error:
                    print(f"Decode error (trying old method): {decode_error}")
                    
                    # Thử phương pháp cũ cho tương thích ngược
                    try:
                        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                        from cryptography.hazmat.backends import default_backend
                        
                        # Sử dụng key cũ với padding space
                        cipher = Cipher(algorithms.AES(crypto.key), modes.CBC(crypto.iv), backend=default_backend())
                        decryptor = cipher.decryptor()
                        decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
                        decrypted_old = decrypted_padded.decode('utf-8').rstrip()
                        return json.loads(decrypted_old)
                    except Exception as old_error:
                        print(f"Old method also failed: {old_error}")
                        
                        # Thử parse JSON trực tiếp
                        try:
                            return json.loads(tx_data)
                        except:
                            return None
                            
            elif isinstance(tx_data, dict):
                return tx_data
            else:
                return None
                
        except Exception as e:
            print(f"Transaction decode error: {e}")
            return None

    def validate_and_fix_blockchain(self):
        """Kiểm tra và sửa các transaction bị lỗi trong blockchain"""
        print("Validating and fixing blockchain...")
        
        try:
            from backend.crypto_utils import CryptoUtils
            crypto = CryptoUtils()
        except:
            print("Cannot load crypto utils")
            return False
        
        fixed_count = 0
        error_count = 0
        
        for block_idx, block in enumerate(self.chain):
            for tx_idx, tx_data in enumerate(block.transactions):
                try:
                    # Thử decode transaction
                    decoded = self._decode_transaction(tx_data, crypto)
                    if decoded is None:
                        error_count += 1
                        print(f"Cannot decode transaction in block {block_idx}, tx {tx_idx}")
                    else:
                        fixed_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error in block {block_idx}, tx {tx_idx}: {e}")
        
        print(f"Validation complete: {fixed_count} valid, {error_count} errors")
        return error_count == 0


    def get_blockchain_info(self):
        """Lấy thông tin tổng quan về blockchain"""
        return {
            'total_blocks': len(self.chain),
            'blockchain_file': self.blockchain_file,
            'backup_file': self.backup_file,
            'file_exists': os.path.exists(self.blockchain_file),
            'backup_exists': os.path.exists(self.backup_file),
            'chain_valid': self.validate_chain(),
            'last_block_time': datetime.fromtimestamp(self.get_latest_block().timestamp).strftime('%Y-%m-%d %H:%M:%S') if self.chain else None
        }
class Transaction:
    def __init__(self, sender, receiver, amount, signature):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount  # SalaryData object
        self.signature = signature

    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount.to_dict(),
            "signature": self.signature
        }

    @staticmethod
    def from_dict(data):
        return Transaction(
            sender=data['sender'],
            receiver=data['receiver'],
            amount=SalaryData.from_dict(data['amount']),
            signature=data['signature']
        )

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current.compute_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True