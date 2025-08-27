//
//  E2EEncryption.swift
//  shareify
//
//  Created for end-to-end encryption support
//

import Foundation
import CryptoKit
import Security

class ShareifyE2EEncryption: ObservableObject {
    private var sessionKey: SymmetricKey?
    private var serverPublicKey: SecKey?
    
    static let shared = ShareifyE2EEncryption()
    
    private init() {}
    
    // MARK: - Key Exchange
    
    func establishSessionWithServer(serverPublicKeyPEM: String, completion: @escaping (Bool) -> Void) {
        guard let serverPublicKey = loadPublicKey(from: serverPublicKeyPEM) else {
            print("Failed to load server public key")
            completion(false)
            return
        }
        
        self.serverPublicKey = serverPublicKey
        
        // Generate a new session key
        self.sessionKey = SymmetricKey(size: .bits256)
        
        // Encrypt session key with server's public key
        guard let encryptedSessionKey = encryptSessionKey() else {
            print("Failed to encrypt session key")
            completion(false)
            return
        }
        
        // Send encrypted session key to server via key exchange endpoint
        sendSessionKeyToServer(encryptedSessionKey: encryptedSessionKey) { success in
            completion(success)
        }
    }
    
    private func loadPublicKey(from pemString: String) -> SecKey? {
        guard let pemData = Data(base64Encoded: pemString),
              let pemString = String(data: pemData, encoding: .utf8) else {
            return nil
        }
        
        // Remove PEM headers/footers and whitespace
        let cleanKey = pemString
            .replacingOccurrences(of: "-----BEGIN PUBLIC KEY-----", with: "")
            .replacingOccurrences(of: "-----END PUBLIC KEY-----", with: "")
            .replacingOccurrences(of: "\n", with: "")
            .replacingOccurrences(of: "\r", with: "")
            .replacingOccurrences(of: " ", with: "")
        
        guard let keyData = Data(base64Encoded: cleanKey) else {
            return nil
        }
        
        let attributes: [String: Any] = [
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeyClass as String: kSecAttrKeyClassPublic,
            kSecAttrKeySizeInBits as String: 2048
        ]
        
        var error: Unmanaged<CFError>?
        guard let publicKey = SecKeyCreateWithData(keyData as CFData, attributes as CFDictionary, &error) else {
            if let error = error?.takeRetainedValue() {
                print("Failed to create public key: \(error)")
            }
            return nil
        }
        
        return publicKey
    }
    
    private func encryptSessionKey() -> String? {
        guard let sessionKey = self.sessionKey,
              let serverPublicKey = self.serverPublicKey else {
            return nil
        }
        
        let sessionKeyData = sessionKey.withUnsafeBytes { Data($0) }
        
        var error: Unmanaged<CFError>?
        guard let encryptedData = SecKeyCreateEncryptedData(
            serverPublicKey,
            .rsaEncryptionOAEPSHA256,
            sessionKeyData as CFData,
            &error
        ) else {
            if let error = error?.takeRetainedValue() {
                print("Failed to encrypt session key: \(error)")
            }
            return nil
        }
        
        return (encryptedData as Data).base64EncodedString()
    }
    
    private func sendSessionKeyToServer(encryptedSessionKey: String, completion: @escaping (Bool) -> Void) {
        // This would be called via ServerManager to establish the session key
        // For now, store it for when we implement the key exchange endpoint
        UserDefaults.standard.set(encryptedSessionKey, forKey: "encrypted_session_key")
        completion(true)
    }
    
    // MARK: - Encryption/Decryption
    
    func encryptPayload(_ data: [String: Any]) -> String? {
        guard let sessionKey = self.sessionKey else {
            print("No session key available for encryption")
            return nil
        }
        
        do {
            let jsonData = try JSONSerialization.data(withJSONObject: data)
            
            // Generate nonce for AES-GCM
            let nonce = AES.GCM.Nonce()
            
            // Encrypt data
            let sealedBox = try AES.GCM.seal(jsonData, using: sessionKey, nonce: nonce)
            
            // Combine nonce and ciphertext
            var combinedData = Data()
            combinedData.append(nonce.withUnsafeBytes { Data($0) })
            combinedData.append(sealedBox.ciphertext)
            combinedData.append(sealedBox.tag)
            
            return combinedData.base64EncodedString()
            
        } catch {
            print("Failed to encrypt payload: \(error)")
            return nil
        }
    }
    
    func decryptPayload(_ encryptedData: String) -> [String: Any]? {
        guard let sessionKey = self.sessionKey,
              let data = Data(base64Encoded: encryptedData) else {
            print("No session key or invalid encrypted data")
            return nil
        }
        
        do {
            // Extract nonce (12 bytes), ciphertext and tag (last 16 bytes)
            let nonceData = data.prefix(12)
            let tagData = data.suffix(16)
            let ciphertextData = data.dropFirst(12).dropLast(16)
            
            let nonce = try AES.GCM.Nonce(data: nonceData)
            let sealedBox = try AES.GCM.SealedBox(nonce: nonce, ciphertext: ciphertextData, tag: tagData)
            
            // Decrypt
            let decryptedData = try AES.GCM.open(sealedBox, using: sessionKey)
            
            // Parse JSON
            let jsonObject = try JSONSerialization.jsonObject(with: decryptedData)
            return jsonObject as? [String: Any]
            
        } catch {
            print("Failed to decrypt payload: \(error)")
            return nil
        }
    }
    
    // MARK: - Utility Methods
    
    func hasSessionKey() -> Bool {
        return sessionKey != nil
    }
    
    func clearSession() {
        sessionKey = nil
        serverPublicKey = nil
        UserDefaults.standard.removeObject(forKey: "encrypted_session_key")
    }
}