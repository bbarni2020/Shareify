#!/usr/bin/env python3
"""
Verify that bridge cannot see decrypted content during E2E encryption
This test simulates the bridge intercepting and logging all traffic
"""

import json
import base64
import sys
import os

# Mock the bridge behavior to capture and analyze traffic
class BridgeInterceptor:
    """Simulates bridge behavior that tries to read encrypted content"""
    
    def __init__(self):
        self.intercepted_messages = []
        self.decryption_attempts = []
    
    def intercept_message(self, message_type, data):
        """Simulate bridge intercepting a message"""
        self.intercepted_messages.append({
            'type': message_type,
            'data': data,
            'analysis': self.analyze_data(data)
        })
        
        print(f"🕵️  Bridge intercepted {message_type}: {len(str(data))} bytes")
    
    def analyze_data(self, data):
        """Attempt to extract sensitive information (simulating malicious bridge)"""
        analysis = {
            'readable_text': [],
            'potential_secrets': [],
            'structured_data': None
        }
        
        try:
            # Try to parse as JSON
            if isinstance(data, dict):
                analysis['structured_data'] = data
                
                # Look for encrypted fields
                if 'body' in data and isinstance(data['body'], str):
                    if len(data['body']) > 100 and data['body'].isalnum():
                        # Looks like base64 encrypted data
                        try:
                            decoded = base64.b64decode(data['body'])
                            # Try to find readable text in decoded data
                            readable_parts = [b for b in decoded if 32 <= b <= 126]
                            if len(readable_parts) < len(decoded) * 0.3:  # Mostly unreadable = encrypted
                                analysis['readable_text'].append("Encrypted payload detected - cannot read")
                            else:
                                analysis['readable_text'].append("Potentially readable content found!")
                        except:
                            analysis['readable_text'].append("Base64 decode failed - likely encrypted")
                    else:
                        # Regular JSON body
                        self._extract_sensitive_info(data['body'], analysis)
                
                # Look for other sensitive fields
                for key, value in data.items():
                    if key.lower() in ['password', 'secret', 'key', 'token']:
                        analysis['potential_secrets'].append(f"{key}: {value}")
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _extract_sensitive_info(self, obj, analysis):
        """Recursively extract potentially sensitive information"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'private', 'key']):
                    analysis['potential_secrets'].append(f"{key}: {value}")
                elif isinstance(value, str) and len(value) > 10:
                    analysis['readable_text'].append(f"{key}: {value[:50]}...")
                elif isinstance(value, (dict, list)):
                    self._extract_sensitive_info(value, analysis)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_sensitive_info(item, analysis)
    
    def generate_report(self):
        """Generate security analysis report"""
        print("\n" + "="*60)
        print("🔍 BRIDGE INTERCEPTION ANALYSIS REPORT")
        print("="*60)
        
        total_messages = len(self.intercepted_messages)
        readable_content = 0
        encrypted_content = 0
        
        for i, msg in enumerate(self.intercepted_messages, 1):
            print(f"\n📨 Message {i}/{total_messages}: {msg['type']}")
            analysis = msg['analysis']
            
            if analysis.get('readable_text'):
                print("  🚨 READABLE CONTENT FOUND:")
                for text in analysis['readable_text']:
                    if "cannot read" in text.lower() or "encrypted" in text.lower():
                        encrypted_content += 1
                        print(f"    ✅ {text}")
                    else:
                        readable_content += 1
                        print(f"    ⚠️  {text}")
            
            if analysis.get('potential_secrets'):
                print("  🔑 POTENTIAL SECRETS:")
                for secret in analysis['potential_secrets']:
                    print(f"    ⚠️  {secret}")
            
            if analysis.get('structured_data'):
                data = analysis['structured_data']
                print(f"  📊 METADATA VISIBLE:")
                for key in ['command', 'method', 'encrypted', 'client_id']:
                    if key in data:
                        print(f"    📋 {key}: {data[key]}")
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total messages intercepted: {total_messages}")
        print(f"  Messages with encrypted content: {encrypted_content}")
        print(f"  Messages with readable content: {readable_content}")
        print(f"  Encryption effectiveness: {(encrypted_content/(encrypted_content+readable_content)*100):.1f}%" if (encrypted_content+readable_content) > 0 else "N/A")
        
        if readable_content == 0:
            print("\n✅ SUCCESS: Bridge cannot read sensitive content!")
            print("   All payload data appears to be properly encrypted.")
        else:
            print("\n❌ SECURITY ISSUE: Bridge can read some content!")
            print("   This indicates encryption is not working properly.")
        
        return readable_content == 0

def test_bridge_cannot_read_content():
    """Test that demonstrates bridge cannot read encrypted content"""
    
    print("Testing Bridge Content Isolation...")
    print("="*50)
    
    # Create bridge interceptor
    bridge = BridgeInterceptor()
    
    # Add path for our encryption module
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from e2e_encryption import get_encryption_instance
        
        # Simulate E2E encryption setup
        print("\n1. Setting up E2E encryption...")
        encryption = get_encryption_instance()
        client_id = "test_client_verification"
        
        # Set up session key (simulate successful key exchange)
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        import base64
        import secrets
        
        session_key = secrets.token_bytes(32)
        encrypted_session_key = encryption.public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        encrypted_session_key_b64 = base64.b64encode(encrypted_session_key).decode()
        
        success = encryption.establish_session_key(client_id, encrypted_session_key_b64)
        print(f"✓ Session established: {success}")
        
        # Test 1: Encrypted request
        print("\n2. Testing encrypted request...")
        sensitive_request = {
            "username": "admin",
            "password": "super_secret_password_123",
            "credit_card": "4532-1234-5678-9012",
            "personal_data": {
                "ssn": "123-45-6789",
                "bank_account": "987654321",
                "private_notes": "This contains very sensitive information that should never be visible to the bridge!"
            }
        }
        
        encrypted_body = encryption.encrypt_payload(client_id, sensitive_request)
        
        # Simulate message going through bridge
        bridge_message = {
            "command": "/user/login",
            "method": "POST", 
            "body": encrypted_body,
            "encrypted": True,
            "client_id": client_id,
            "wait_time": 2
        }
        
        bridge.intercept_message("execute_command", bridge_message)
        
        # Test 2: Encrypted response
        print("\n3. Testing encrypted response...")
        sensitive_response = {
            "success": True,
            "user_data": {
                "email": "user@example.com",
                "api_key": "sk_live_abcdef123456789",
                "private_files": [
                    "/home/user/secret_document.pdf",
                    "/private/financial_records.xlsx"
                ]
            },
            "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sensitive_payload",
            "internal_notes": "This user has administrative privileges"
        }
        
        encrypted_response = encryption.encrypt_payload(client_id, sensitive_response)
        
        response_message = {
            "command_id": "cmd_12345",
            "response": encrypted_response,
            "encrypted": True,
            "client_id": client_id
        }
        
        bridge.intercept_message("command_response", response_message)
        
        # Test 3: Unencrypted message for comparison
        print("\n4. Testing unencrypted message for comparison...")
        unencrypted_message = {
            "command": "/user/get_profile",
            "method": "GET",
            "body": {
                "username": "admin",
                "include_sensitive": True,
                "access_token": "bearer_token_12345"
            }
        }
        
        bridge.intercept_message("execute_command_unencrypted", unencrypted_message)
        
        # Generate analysis report
        return bridge.generate_report()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure cryptography library is installed")
        return False
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔒 SHAREIFY E2E ENCRYPTION VERIFICATION")
    print("Testing that bridge cannot access decrypted content")
    print()
    
    success = test_bridge_cannot_read_content()
    
    if success:
        print("\n🎉 VERIFICATION PASSED!")
        print("The bridge service cannot read encrypted content.")
        print("End-to-end encryption is working correctly.")
    else:
        print("\n❌ VERIFICATION FAILED!")
        print("The bridge may be able to read some content.")
        print("Please review the encryption implementation.")
    
    sys.exit(0 if success else 1)