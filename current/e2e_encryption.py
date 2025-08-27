"""
End-to-End Encryption Module for Shareify
Provides RSA key exchange and AES-GCM encryption for secure communication between iOS app and local server
"""

import os
import json
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
import secrets


class ShareifyE2EEncryption:
    """
    Handles end-to-end encryption for Shareify communications.
    Uses RSA for key exchange and AES-GCM for payload encryption.
    """
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.session_keys = {}  # Maps client_id -> AES key
        self._ensure_keys()
    
    def _ensure_keys(self):
        """Generate or load RSA key pair"""
        key_file = "settings/e2e_keys.json"
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    key_data = json.load(f)
                
                self.private_key = serialization.load_pem_private_key(
                    base64.b64decode(key_data['private_key']),
                    password=None,
                    backend=default_backend()
                )
                self.public_key = self.private_key.public_key()
                return
            except Exception as e:
                print(f"Failed to load existing keys: {e}, generating new ones")
        
        # Generate new key pair
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
        # Save keys
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        key_data = {
            'private_key': base64.b64encode(private_pem).decode(),
            'generated_at': str(os.time.time() if hasattr(os, 'time') else 0)
        }
        
        with open(key_file, 'w') as f:
            json.dump(key_data, f, indent=2)
    
    def get_public_key_pem(self):
        """Get public key in PEM format for sharing"""
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(public_pem).decode()
    
    def establish_session_key(self, client_id, encrypted_session_key):
        """
        Decrypt the session key sent by client and store it
        Returns True if successful
        """
        try:
            # Decrypt the session key using our private key
            session_key = self.private_key.decrypt(
                base64.b64decode(encrypted_session_key),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            self.session_keys[client_id] = session_key
            print(f"Established session key for client {client_id}")
            return True
            
        except Exception as e:
            print(f"Failed to establish session key for {client_id}: {e}")
            return False
    
    def encrypt_payload(self, client_id, data):
        """
        Encrypt data using the session key for the given client
        Returns base64 encoded encrypted data or None if no session key
        """
        if client_id not in self.session_keys:
            print(f"No session key for client {client_id}")
            return None
        
        try:
            # Convert data to JSON if it's not already a string
            if not isinstance(data, str):
                data = json.dumps(data)
            
            # Generate nonce and encrypt
            aesgcm = AESGCM(self.session_keys[client_id])
            nonce = os.urandom(12)  # GCM standard nonce size
            ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
            
            # Combine nonce and ciphertext
            encrypted_data = nonce + ciphertext
            
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            print(f"Failed to encrypt payload for {client_id}: {e}")
            return None
    
    def decrypt_payload(self, client_id, encrypted_data):
        """
        Decrypt data using the session key for the given client
        Returns decrypted data or None if decryption fails
        """
        if client_id not in self.session_keys:
            print(f"No session key for client {client_id}")
            return None
        
        try:
            # Decode base64 and split nonce/ciphertext
            encrypted_bytes = base64.b64decode(encrypted_data)
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # Decrypt
            aesgcm = AESGCM(self.session_keys[client_id])
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON, return as string if it fails
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
                
        except Exception as e:
            print(f"Failed to decrypt payload for {client_id}: {e}")
            return None
    
    def remove_session_key(self, client_id):
        """Remove session key for a client"""
        if client_id in self.session_keys:
            del self.session_keys[client_id]
            print(f"Removed session key for client {client_id}")


# Global instance
_encryption_instance = None

def get_encryption_instance():
    """Get the global encryption instance"""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = ShareifyE2EEncryption()
    return _encryption_instance