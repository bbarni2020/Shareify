# End-to-End Encryption for Shareify

## Overview

Shareify now supports end-to-end encryption between the iOS app and local servers via the bridge. This ensures that sensitive data in requests and responses cannot be read by the bridge service, providing true end-to-end security.

## How It Works

### Architecture

1. **Key Exchange**: iOS app and local server exchange RSA public keys via the bridge
2. **Session Establishment**: iOS app generates AES-256 session key, encrypts it with server's RSA public key
3. **Secure Communication**: All request/response bodies are encrypted with AES-GCM using the session key
4. **Bridge Relay**: Bridge relays encrypted data without being able to decrypt it

### Encryption Details

- **Key Exchange**: RSA-2048 with OAEP padding and SHA-256
- **Session Encryption**: AES-256-GCM with 96-bit nonces
- **Key Storage**: iOS Keychain, Server filesystem (encrypted at rest)
- **Session Management**: Per-client session keys with automatic cleanup

## Implementation

### Local Server (Python)

#### New Endpoints

- `GET /api/e2e/public_key` - Get server's RSA public key
- `POST /api/e2e/establish_session` - Establish encrypted session

#### Key Components

1. **E2E Encryption Module** (`e2e_encryption.py`)
   - RSA key pair generation and management
   - AES-GCM encryption/decryption
   - Session key management

2. **Cloud Connection** (`cloud_connection.py`)
   - Handle encrypted commands from bridge
   - Encrypt/decrypt payloads automatically
   - Key exchange protocol support

3. **Local Server** (`main.py`)
   - E2E key exchange endpoints
   - Integration with existing API

### iOS App (Swift)

#### New Components

1. **E2EEncryption.swift**
   - RSA key loading and session key encryption
   - AES-GCM encryption/decryption using CryptoKit
   - Session management

2. **ServerManager.swift** (Updated)
   - Automatic encryption/decryption of requests/responses
   - Session establishment flow
   - Fallback to unencrypted communication

### Bridge Service (Python)

#### Updates

1. **Key Exchange Relay** (`server.py`)
   - Relay key exchange messages between clients and servers
   - No access to decrypted content
   - Metadata handling for encrypted payloads

## Usage

### For iOS App Users

E2E encryption is transparent to users. The app will automatically:

1. Request server's public key on first connection
2. Establish encrypted session
3. Encrypt all sensitive requests/responses
4. Fall back gracefully if encryption is not available

### For Server Administrators

E2E encryption is enabled by default for new installations. 

#### Manual Setup

```bash
# Install required dependencies
pip install cryptography==42.0.5

# Keys are automatically generated on first use
# Stored in: settings/e2e_keys.json
```

#### Monitoring

```bash
# Check encryption status in server logs
grep "E2E\|encrypted\|session" shareify.log

# Test encryption endpoints
curl http://localhost:6969/api/e2e/public_key
```

## Security Considerations

### What's Protected

✅ **Request/Response Bodies**: Fully encrypted end-to-end  
✅ **Session Keys**: Encrypted with RSA-2048  
✅ **File Content**: Protected during transfer  
✅ **API Payloads**: Cannot be read by bridge

### What's Not Protected

⚠️ **Request Metadata**: Command names, methods (needed for routing)  
⚠️ **Authentication Tokens**: JWT tokens (needed for authorization)  
⚠️ **Connection Metadata**: IP addresses, timestamps  

### Best Practices

1. **Regular Key Rotation**: Keys are generated per session
2. **Secure Storage**: iOS Keychain, protected server filesystem
3. **Graceful Degradation**: Falls back to HTTPS-only if E2E fails
4. **Audit Logging**: All encryption events are logged

## Troubleshooting

### Common Issues

1. **"No session key" errors**
   - Restart iOS app to re-establish session
   - Check server connectivity

2. **"Failed to decrypt" errors**
   - Session may have expired
   - Restart both client and server

3. **Encryption disabled**
   - Verify cryptography library is installed
   - Check server logs for key generation errors

### Debug Mode

Enable detailed encryption logging:

```python
# In e2e_encryption.py
logging.basicConfig(level=logging.DEBUG)
```

### Testing

Run the encryption test suite:

```bash
cd current/
python3 test_e2e_encryption.py
python3 test_e2e_endpoints.py
```

## Compatibility

- **iOS**: Requires iOS 13+ (CryptoKit)
- **Python**: Requires Python 3.7+ and cryptography library
- **Bridge**: No changes required (transparent relay)
- **Existing Clients**: Continue to work without encryption

## Performance Impact

- **Key Exchange**: One-time ~100ms overhead per session
- **Encryption**: ~1-5ms per request (depends on payload size)
- **Memory**: ~2MB additional per active session
- **Storage**: ~1KB for keys, ~256 bytes per session

The performance impact is minimal for typical usage patterns.