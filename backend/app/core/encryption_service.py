"""
Encryption Service

This service provides data encryption and decryption functionality
for sensitive information in the Galactic Empire game.
"""

import base64
import hashlib
import secrets
import time
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..core.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        # Generate or use existing encryption key
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key from settings"""
        # In production, this should be stored securely (environment variable, key management service)
        secret_key = getattr(settings, 'encryption_key', None)
        
        if not secret_key:
            # Generate a new key (should be stored persistently in production)
            secret_key = settings.secret_key
        
        # Derive encryption key from secret
        password = secret_key.encode()
        salt = b'galactic_empire_salt'  # In production, use a random salt stored securely
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_string(self, plaintext: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        if not plaintext:
            return ""
        
        try:
            encrypted_bytes = self.fernet.encrypt(plaintext.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception:
            # If encryption fails, return empty string (don't expose errors)
            return ""
    
    def decrypt_string(self, encrypted_text: str) -> str:
        """Decrypt a base64 encoded encrypted string"""
        if not encrypted_text:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # If decryption fails, return empty string (don't expose errors)
            return ""
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary as JSON"""
        if not data:
            return ""
        
        try:
            import json
            json_string = json.dumps(data, sort_keys=True)
            return self.encrypt_string(json_string)
        except Exception:
            return ""
    
    def decrypt_dict(self, encrypted_text: str) -> Dict[str, Any]:
        """Decrypt an encrypted dictionary"""
        if not encrypted_text:
            return {}
        
        try:
            import json
            json_string = self.decrypt_string(encrypted_text)
            if json_string:
                return json.loads(json_string)
        except Exception:
            pass
        
        return {}
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> tuple:
        """Hash a password with salt (returns hash, salt)"""
        if not salt:
            salt = secrets.token_urlsafe(32)
        
        # Use PBKDF2 for password hashing
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=100000,
        )
        
        hash_bytes = kdf.derive(password_bytes)
        password_hash = base64.urlsafe_b64encode(hash_bytes).decode('utf-8')
        
        return password_hash, salt
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify a password against its hash"""
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return computed_hash == password_hash
        except Exception:
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self) -> tuple:
        """Generate an API key and its hash (returns key, hash, prefix)"""
        # Generate random key
        api_key = secrets.token_urlsafe(32)
        
        # Create hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Create prefix for identification (first 8 characters)
        key_prefix = api_key[:8]
        
        return api_key, key_hash, key_prefix
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in a data dictionary"""
        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'api_key',
            'private_key', 'session_token', 'refresh_token'
        }
        
        encrypted_data = data.copy()
        
        for field, value in data.items():
            if any(sensitive_word in field.lower() for sensitive_word in sensitive_fields):
                if isinstance(value, str) and value:
                    encrypted_data[field] = self.encrypt_string(value)
        
        return encrypted_data
    
    def decrypt_sensitive_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in a data dictionary"""
        sensitive_fields = {
            'password', 'token', 'secret', 'key', 'api_key',
            'private_key', 'session_token', 'refresh_token'
        }
        
        decrypted_data = encrypted_data.copy()
        
        for field, value in encrypted_data.items():
            if any(sensitive_word in field.lower() for sensitive_word in sensitive_fields):
                if isinstance(value, str) and value:
                    decrypted_data[field] = self.decrypt_string(value)
        
        return decrypted_data
    
    def create_secure_session_data(self, user_id: int, additional_data: Dict[str, Any] = None) -> str:
        """Create encrypted session data"""
        session_data = {
            'user_id': user_id,
            'created_at': int(time.time()),
            'expires_at': int(time.time()) + 86400,  # 24 hours
        }
        
        if additional_data:
            session_data.update(additional_data)
        
        return self.encrypt_dict(session_data)
    
    def validate_secure_session_data(self, encrypted_session_data: str) -> Optional[Dict[str, Any]]:
        """Validate and decrypt session data"""
        session_data = self.decrypt_dict(encrypted_session_data)
        
        if not session_data:
            return None
        
        # Check expiration
        expires_at = session_data.get('expires_at', 0)
        if expires_at < int(time.time()):
            return None
        
        return session_data


# Global encryption service instance
encryption_service = EncryptionService()
