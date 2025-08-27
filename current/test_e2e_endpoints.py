#!/usr/bin/env python3
"""
Test E2E encryption endpoints on local server
"""

import requests
import json
import time
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from e2e_encryption import get_encryption_instance

def test_e2e_endpoints():
    print("Testing E2E encryption endpoints...")
    
    base_url = "http://127.0.0.1:6969"  # Default Shareify local server port
    
    try:
        # Test 1: Check if server is running
        print("\n1. Testing server connectivity...")
        try:
            response = requests.get(f"{base_url}/api/is_up", timeout=5)
            if response.status_code == 200:
                print("✓ Server is running")
            else:
                print(f"✗ Server returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            print("✗ Server is not running. Please start the Shareify server first.")
            print("  Run: python3 main.py")
            return False
        
        # Test 2: Get public key
        print("\n2. Testing public key endpoint...")
        try:
            response = requests.get(f"{base_url}/api/e2e/public_key", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('public_key'):
                    print(f"✓ Public key retrieved (length: {len(data['public_key'])})")
                    server_public_key = data['public_key']
                else:
                    print(f"✗ Invalid public key response: {data}")
                    return False
            else:
                print(f"✗ Public key request failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Public key request failed: {e}")
            return False
        
        # Test 3: Establish session (simulate client behavior)
        print("\n3. Testing session establishment...")
        try:
            # Create a client-side encryption instance to simulate client behavior
            import tempfile
            import shutil
            
            # Create temporary directory for client keys
            temp_dir = tempfile.mkdtemp()
            original_dir = os.getcwd()
            
            try:
                os.chdir(temp_dir)
                client_encryption = get_encryption_instance()
                
                # Generate session key and encrypt with server's public key
                from cryptography.hazmat.primitives import serialization, hashes
                from cryptography.hazmat.primitives.asymmetric import padding
                import base64
                import secrets
                
                # Load server's public key
                server_key_data = base64.b64decode(server_public_key)
                server_key_obj = serialization.load_pem_public_key(server_key_data)
                
                # Generate session key
                session_key = secrets.token_bytes(32)
                
                # Encrypt with server's public key
                encrypted_session_key = server_key_obj.encrypt(
                    session_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                encrypted_session_key_b64 = base64.b64encode(encrypted_session_key).decode()
                
                # Send session establishment request
                client_id = "test_client_12345"
                session_data = {
                    "client_id": client_id,
                    "encrypted_session_key": encrypted_session_key_b64
                }
                
                response = requests.post(
                    f"{base_url}/api/e2e/establish_session",
                    json=session_data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print(f"✓ Session established successfully")
                    else:
                        print(f"✗ Session establishment failed: {data.get('error')}")
                        return False
                else:
                    print(f"✗ Session establishment failed with status: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            finally:
                os.chdir(original_dir)
                shutil.rmtree(temp_dir)
                
        except Exception as e:
            print(f"✗ Session establishment test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n🎉 All E2E endpoint tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_e2e_endpoints()
    sys.exit(0 if success else 1)