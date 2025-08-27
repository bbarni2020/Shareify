#!/usr/bin/env python3
"""
Test script for E2E encryption functionality
"""

import os
import sys
import json
import shutil

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Clean up any existing test keys
test_settings_dir = "settings"
if os.path.exists(test_settings_dir):
    shutil.rmtree(test_settings_dir)

try:
    from e2e_encryption import get_encryption_instance
    
    print("Testing E2E Encryption Module...")
    
    # Test 1: Initialize encryption
    print("\n1. Testing encryption initialization...")
    encryption = get_encryption_instance()
    print(f"✓ Encryption instance created")
    
    # Test 2: Get public key
    print("\n2. Testing public key generation...")
    public_key = encryption.get_public_key_pem()
    print(f"✓ Public key generated (length: {len(public_key)})")
    
    # Test 3: Session key establishment
    print("\n3. Testing session key establishment...")
    
    # Simulate a session key from client (this would normally be encrypted with our public key)
    # For testing, we'll manually set up a session key
    test_client_id = "test_client_123"
    
    # Create a dummy encrypted session key (in real scenario, this would be properly encrypted)
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    import base64
    import secrets
    
    # Generate a test session key
    test_session_key = secrets.token_bytes(32)  # 256-bit key for AES
    
    # Encrypt it with our own public key (simulating client behavior)
    public_key_obj = encryption.public_key
    encrypted_session_key = public_key_obj.encrypt(
        test_session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    encrypted_session_key_b64 = base64.b64encode(encrypted_session_key).decode()
    
    # Test session key establishment
    success = encryption.establish_session_key(test_client_id, encrypted_session_key_b64)
    print(f"✓ Session key establishment: {success}")
    
    # Test 4: Encryption/Decryption
    print("\n4. Testing payload encryption/decryption...")
    
    test_data = {
        "command": "/user/get_self",
        "method": "GET",
        "test_data": "This is sensitive information",
        "numbers": [1, 2, 3, 4, 5],
        "nested": {
            "key": "value",
            "another": "test"
        }
    }
    
    # Encrypt
    encrypted_payload = encryption.encrypt_payload(test_client_id, test_data)
    if encrypted_payload:
        print(f"✓ Payload encrypted (length: {len(encrypted_payload)})")
    else:
        print("✗ Failed to encrypt payload")
        sys.exit(1)
    
    # Decrypt
    decrypted_payload = encryption.decrypt_payload(test_client_id, encrypted_payload)
    if decrypted_payload == test_data:
        print(f"✓ Payload decrypted successfully")
        print(f"  Original: {test_data}")
        print(f"  Decrypted: {decrypted_payload}")
    else:
        print("✗ Decryption failed or data mismatch")
        print(f"  Original: {test_data}")
        print(f"  Decrypted: {decrypted_payload}")
        sys.exit(1)
    
    # Test 5: String payload
    print("\n5. Testing string payload...")
    test_string = "Simple string payload"
    encrypted_string = encryption.encrypt_payload(test_client_id, test_string)
    decrypted_string = encryption.decrypt_payload(test_client_id, encrypted_string)
    
    if decrypted_string == test_string:
        print(f"✓ String payload encryption/decryption successful")
    else:
        print(f"✗ String payload test failed")
        sys.exit(1)
    
    # Test 6: Invalid client
    print("\n6. Testing invalid client ID...")
    invalid_result = encryption.encrypt_payload("invalid_client", test_data)
    if invalid_result is None:
        print("✓ Correctly rejected encryption for invalid client")
    else:
        print("✗ Should have rejected invalid client")
        sys.exit(1)
    
    # Test 7: Session removal
    print("\n7. Testing session removal...")
    encryption.remove_session_key(test_client_id)
    removed_result = encryption.encrypt_payload(test_client_id, test_data)
    if removed_result is None:
        print("✓ Session key removal successful")
    else:
        print("✗ Session key should have been removed")
        sys.exit(1)
    
    print("\n🎉 All tests passed! E2E encryption is working correctly.")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install required dependencies: pip install cryptography")
    sys.exit(1)
except Exception as e:
    print(f"Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Clean up test files
    if os.path.exists(test_settings_dir):
        shutil.rmtree(test_settings_dir)
    print("\nTest cleanup completed.")