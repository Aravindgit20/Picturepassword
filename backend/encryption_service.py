# Encryption Service
# Handles coordinate encryption and password hashing

import hashlib
import bcrypt
import json
from cryptography.fernet import Fernet
from backend.config import Config

class EncryptionService:
    """Service for encrypting/decrypting coordinates and hashing passwords"""
    
    def __init__(self):
        self.cipher_suite = Fernet(Config.ENCRYPTION_KEY)
    
    def encrypt_coordinates(self, coordinates):
        """Encrypt click coordinates for secure storage"""
        try:
            coord_json = json.dumps(coordinates)
            encrypted_data = self.cipher_suite.encrypt(coord_json.encode())
            return encrypted_data.decode()
        except Exception as e:
            print(f"Error encrypting coordinates: {e}")
            return None
    
    def decrypt_coordinates(self, encrypted_data):
        """Decrypt stored click coordinates"""
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Error decrypting coordinates: {e}")
            return None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with a random salt"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password — supports bcrypt and legacy SHA-256 hashes"""
        if password_hash.startswith('$2'):
            # bcrypt hash
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        # Legacy SHA-256 fallback
        return hashlib.sha256(password.encode()).hexdigest() == password_hash


# Global instance
encryption_service = EncryptionService()
