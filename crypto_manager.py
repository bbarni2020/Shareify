from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import base64
import secrets
import json
import os
from pathlib import Path


class CryptoManager:
    def __init__(self, keys_dir=None):
        if keys_dir is None:
            keys_dir = Path(__file__).parent / "settings" / "keys"
        
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        
        self.private_key_path = self.keys_dir / "server_private.pem"
        self.public_key_path = self.keys_dir / "server_public.pem"
        self.session_keys_path = self.keys_dir / "session_keys.json"
        
        self.private_key = None
        self.public_key = None
        self.session_keys = {}
        
        self._load_or_generate_rsa_keys()
        self._load_session_keys()
    
    def _load_or_generate_rsa_keys(self):
        if self.private_key_path.exists() and self.public_key_path.exists():
            try:
                with open(self.private_key_path, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None,
                        backend=default_backend()
                    )
                
                with open(self.public_key_path, 'rb') as f:
                    self.public_key = serialization.load_pem_public_key(
                        f.read(),
                        backend=default_backend()
                    )
                return
            except Exception:
                pass
        
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        with open(self.private_key_path, 'wb') as f:
            f.write(private_pem)
        os.chmod(self.private_key_path, 0o600)
        
        with open(self.public_key_path, 'wb') as f:
            f.write(public_pem)
    
    def _load_session_keys(self):
        if self.session_keys_path.exists():
            try:
                with open(self.session_keys_path, 'r') as f:
                    self.session_keys = json.load(f)
            except Exception:
                self.session_keys = {}
    
    def _save_session_keys(self):
        with open(self.session_keys_path, 'w') as f:
            json.dump(self.session_keys, f)
        os.chmod(self.session_keys_path, 0o600)
    
    def get_public_key_pem(self):
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    def decrypt_session_key(self, encrypted_key_b64):
        encrypted_key = base64.b64decode(encrypted_key_b64)
        
        session_key = self.private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return session_key
    
    def generate_session_key(self, client_id):
        session_key = AESGCM.generate_key(bit_length=256)
        session_key_b64 = base64.b64encode(session_key).decode('utf-8')
        
        self.session_keys[client_id] = {
            'key': session_key_b64,
            'created_at': os.times().elapsed
        }
        self._save_session_keys()
        
        return session_key
    
    def get_session_key(self, client_id):
        if client_id not in self.session_keys:
            return None
        
        session_key_b64 = self.session_keys[client_id]['key']
        return base64.b64decode(session_key_b64)
    
    def set_session_key(self, client_id, session_key):
        session_key_b64 = base64.b64encode(session_key).decode('utf-8')
        self.session_keys[client_id] = {
            'key': session_key_b64,
            'created_at': os.times().elapsed
        }
        self._save_session_keys()
    
    def encrypt_data(self, data, session_key):
        if isinstance(data, str):
            data = data.encode('utf-8')
        elif not isinstance(data, bytes):
            data = json.dumps(data).encode('utf-8')
        
        nonce = secrets.token_bytes(12)
        
        aesgcm = AESGCM(session_key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        
        encrypted_package = {
            'nonce': base64.b64encode(nonce).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
        }
        
        return encrypted_package
    
    def decrypt_data(self, encrypted_package, session_key):
        nonce = base64.b64decode(encrypted_package['nonce'])
        ciphertext = base64.b64decode(encrypted_package['ciphertext'])
        
        aesgcm = AESGCM(session_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        return plaintext
    
    def encrypt_response(self, response_data, client_id):
        session_key = self.get_session_key(client_id)
        if not session_key:
            return None
        
        return self.encrypt_data(response_data, session_key)
    
    def decrypt_request(self, encrypted_package, client_id):
        session_key = self.get_session_key(client_id)
        if not session_key:
            return None
        
        plaintext = self.decrypt_data(encrypted_package, session_key)
        
        try:
            return json.loads(plaintext.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return plaintext
    
    def cleanup_old_sessions(self, max_age_seconds=86400):
        current_time = os.times().elapsed
        expired_clients = []
        
        for client_id, session_data in self.session_keys.items():
            created_at = session_data.get('created_at', 0)
            if current_time - created_at > max_age_seconds:
                expired_clients.append(client_id)
        
        for client_id in expired_clients:
            del self.session_keys[client_id]
        
        if expired_clients:
            self._save_session_keys()
        
        return len(expired_clients)
    
    def rotate_session_key(self, client_id):
        new_key = self.generate_session_key(client_id)
        return new_key
