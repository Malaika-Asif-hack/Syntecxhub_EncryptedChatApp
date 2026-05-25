import os
import base64
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class AESChatCrypto:
    """Handles AES encryption/decryption for chat messages"""
    
    def __init__(self, password: str, salt: bytes = None):
        """
        Initialize crypto with password-based key derivation
        Args:
            password: Shared secret password
            salt: Salt for key derivation (generated if not provided)
        """
        self.backend = default_backend()
        self.password = password.encode('utf-8')
        self.logger = logging.getLogger(__name__)
        
        if salt is None:
            self.salt = os.urandom(16)
            self.logger.debug("Generated new random salt for key derivation")
        else:
            self.salt = salt
            self.logger.debug("Using provided salt for key derivation")
            
        # Derive 32-byte key from password using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=self.backend
        )
        self.key = kdf.derive(self.password)
        self.logger.debug("Key derived successfully using PBKDF2 with 100,000 iterations")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a message with AES-CBC
        Returns: Base64 encoded string containing IV + ciphertext
        """
        # Generate random IV (16 bytes for AES)
        iv = os.urandom(16)
        
        # Create AES cipher in CBC mode
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Pad plaintext to AES block size (16 bytes)
        padded_data = self._pad(plaintext.encode('utf-8'))
        
        # Encrypt
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and ciphertext, then base64 encode
        combined = iv + ciphertext
        return base64.b64encode(combined).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a message
        Args: Base64 encoded string containing IV + ciphertext
        Returns: Decrypted plaintext
        """
        # Decode from base64
        combined = base64.b64decode(encrypted_data)
        
        # Extract IV (first 16 bytes) and ciphertext
        iv = combined[:16]
        ciphertext = combined[16:]
        
        # Create AES cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        plaintext = self._unpad(decrypted_padded)
        
        return plaintext.decode('utf-8')
    
    def encrypt_message(self, plaintext: str) -> str:
        """Alias for encrypt() - for compatibility with server code"""
        return self.encrypt(plaintext)
    
    def decrypt_message(self, encrypted_data: str) -> str:
        """Alias for decrypt() - for compatibility with server code"""
        return self.decrypt(encrypted_data)
    
    def _pad(self, data: bytes) -> bytes:
        """Pad data to AES block size (PKCS7)"""
        block_size = 16
        padding_len = block_size - (len(data) % block_size)
        padding = bytes([padding_len] * padding_len)
        return data + padding
    
    def _unpad(self, data: bytes) -> bytes:
        """Remove PKCS7 padding"""
        padding_len = data[-1]
        if padding_len > 16:
            raise ValueError("Invalid padding")
        return data[:-padding_len]
    
    def export_salt(self) -> str:
        """Export salt for sharing with clients"""
        return base64.b64encode(self.salt).decode('utf-8')
    
    @classmethod
    def from_salt(cls, password: str, salt_b64: str):
        """Create crypto instance from existing salt"""
        salt = base64.b64decode(salt_b64)
        return cls(password, salt)


def generate_secure_password() -> str:
    """Generate a secure random password"""
    return base64.b64encode(os.urandom(24)).decode('utf-8')[:32]


# Encryption algorithm information for documentation
ENCRYPTION_INFO = {
    "algorithm": "AES-256-CBC",
    "key_size": 256,
    "block_size": 128,
    "iv_size": 16,
    "key_derivation": "PBKDF2 with SHA256",
    "iterations": 100000,
    "padding": "PKCS7",
    "mode": "CBC"
}

def get_encryption_info() -> dict:
    """Return encryption algorithm information for documentation"""
    return ENCRYPTION_INFO.copy()