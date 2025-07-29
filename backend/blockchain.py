import hashlib
import json
import time
from datetime import datetime
import base64

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

    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty=2):
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
            "transactions": [
                tx.to_dict() if hasattr(tx, "to_dict") else tx
                for tx in self.transactions
            ],
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "nonce": self.nonce
        }

    @staticmethod
    def from_dict(data):
        transactions = [Transaction.from_dict(tx) for tx in data['transactions']]
        block = Block(
            index=data['index'],
            transactions=transactions,
            timestamp=data['timestamp'],
            previous_hash=data['previous_hash'],
            nonce=data.get('nonce', 0)
        )
        block.hash = data['hash']
        return block
    
class Blockchain:
    def __init__(self, difficulty=2):
        self.difficulty = difficulty  # Đặt difficulty trước
        self.chain = []
        self.pending_transactions = []
        self.mining_reward = 10
        self.backup_file = "blockchain_backup.json"
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(0, [], time.time(), "0")
        genesis.mine_block(self.difficulty)
        self.chain.append(genesis)
        self.save_to_file("blockchain.json")
        self.backup_chain()
        return genesis

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
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
            self.save_to_file("blockchain.json")
            return new_block
        else:
            raise Exception("Block không hợp lệ!")

    def save_to_file(self, filename):
        data = [block.to_dict() for block in self.chain]
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            self.chain = [Block.from_dict(b) for b in data]

    def backup_chain(self):
        data = [block.to_dict() for block in self.chain]
        with open(self.backup_file, 'w') as f:
            json.dump(data, f, indent=2)

    def restore_chain(self):
        try:
            with open(self.backup_file, 'r') as f:
                backup_data = json.load(f)
        except FileNotFoundError:
            return []

        restored_blocks = []
        for i, (current_block, original_block) in enumerate(zip(self.chain, backup_data)):
            current_data = current_block.to_dict()
            if current_data != original_block:
                restored = Block.from_dict(original_block)
                self.chain[i] = restored
                restored_blocks.append(i)
        return restored_blocks

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
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if not current_block.validate_block():
                return False
                
            if current_block.previous_hash != previous_block.hash:
                return False
                
        return True

    def add_transaction(self, transaction):
        self.pending_transactions.append(transaction)
        self.save_to_file("blockchain.json")

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
            'latest_block_hash': self.get_latest_block().hash
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

    def search_transactions_by_employee(self, employee_id):
        transactions = []
        for block in self.chain:
            for tx in block.transactions:
                try:
                    # Thử decode transaction
                    tx_dict = self._decode_transaction(tx)
                    if tx_dict and tx_dict.get('employee_id') == employee_id:
                        transactions.append({
                            'block_index': block.index,
                            'transaction': tx_dict,
                            'timestamp': block.timestamp
                        })
                except:
                    continue
        return transactions

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

    def _decode_transaction(self, tx_data, crypto=None):
        """Helper function để decode transaction"""
        try:
            if isinstance(tx_data, str):
                # Thử decode base64 + decrypt
                if crypto:
                    try:
                        encrypted_bytes = base64.b64decode(tx_data)
                        decrypted_json = crypto.aes_decrypt(encrypted_bytes)
                        return json.loads(decrypted_json)
                    except:
                        pass
                
                # Thử parse JSON trực tiếp
                try:
                    return json.loads(tx_data)
                except:
                    return None
                    
            elif isinstance(tx_data, dict):
                return tx_data
            else:
                return None
                
        except:
            return None