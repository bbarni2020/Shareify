import Foundation
import CryptoKit
import Security

class CryptoManager {
    private var privateKey: SecKey?
    private var publicKey: SecKey?
    private var sessionKey: SymmetricKey?
    private let clientId: String
    
    init(clientId: String) {
        self.clientId = clientId
        loadOrGenerateRSAKeyPair()
    }
    
    private func loadOrGenerateRSAKeyPair() {
        let privateTag = "com.shareify.privatekey.\(clientId)".data(using: .utf8)!
        let publicTag = "com.shareify.publickey.\(clientId)".data(using: .utf8)!
        
        let privateQuery: [String: Any] = [
            kSecClass as String: kSecClassKey,
            kSecAttrApplicationTag as String: privateTag,
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecReturnRef as String: true
        ]
        
        var privateItem: CFTypeRef?
        let privateStatus = SecItemCopyMatching(privateQuery as CFDictionary, &privateItem)
        
        if privateStatus == errSecSuccess, let privKey = privateItem as! SecKey? {
            self.privateKey = privKey
            if let pubKey = SecKeyCopyPublicKey(privKey) {
                self.publicKey = pubKey
                print("Loaded existing RSA key pair")
                return
            }
        }
        
        let attributes: [String: Any] = [
            kSecAttrKeyType as String: kSecAttrKeyTypeRSA,
            kSecAttrKeySizeInBits as String: 4096,
            kSecPrivateKeyAttrs as String: [
                kSecAttrIsPermanent as String: true,
                kSecAttrApplicationTag as String: privateTag
            ],
            kSecPublicKeyAttrs as String: [
                kSecAttrIsPermanent as String: true,
                kSecAttrApplicationTag as String: publicTag
            ]
        ]
        
        var error: Unmanaged<CFError>?
        guard let privateKey = SecKeyCreateRandomKey(attributes as CFDictionary, &error),
              let publicKey = SecKeyCopyPublicKey(privateKey) else {
            print("Failed to generate RSA key pair: \(String(describing: error))")
            return
        }
        
        self.privateKey = privateKey
        self.publicKey = publicKey
        print("Generated new RSA-4096 key pair")
    }
    
    func getPublicKeyPEM() -> String? {
        guard let publicKey = publicKey else { return nil }
        
        var error: Unmanaged<CFError>?
        guard let keyData = SecKeyCopyExternalRepresentation(publicKey, &error) as Data? else {
            print("Failed to export public key: \(String(describing: error))")
            return nil
        }
        
        let base64Key = keyData.base64EncodedString()
        let chunks = base64Key.chunked(into: 64)
        let pemKey = """
        -----BEGIN PUBLIC KEY-----
        \(chunks.joined(separator: "\n"))
        -----END PUBLIC KEY-----
        """
        
        return pemKey
    }
    
    func decryptSessionKey(encryptedKeyBase64: String) -> Bool {
        guard let privateKey = privateKey,
              let encryptedData = Data(base64Encoded: encryptedKeyBase64) else {
            print("Missing private key or invalid base64")
            return false
        }
        
        var error: Unmanaged<CFError>?
        guard let decryptedData = SecKeyCreateDecryptedData(
            privateKey,
            .rsaEncryptionOAEPSHA256,
            encryptedData as CFData,
            &error
        ) as Data? else {
            print("Failed to decrypt session key: \(String(describing: error))")
            return false
        }
        
        self.sessionKey = SymmetricKey(data: decryptedData)
        print("Session key decrypted successfully")
        return true
    }
    
    func encryptData(_ data: Data) -> [String: String]? {
        guard let sessionKey = sessionKey else {
            print("No session key available")
            return nil
        }
        
        do {
            let nonce = AES.GCM.Nonce()
            let sealedBox = try AES.GCM.seal(data, using: sessionKey, nonce: nonce)
            
            guard let ciphertext = sealedBox.ciphertext as Data?,
                  let tag = sealedBox.tag as Data? else {
                return nil
            }
            
            let combined = ciphertext + tag
            let nonceData = Data(nonce)
            
            return [
                "nonce": nonceData.base64EncodedString(),
                "ciphertext": combined.base64EncodedString()
            ]
        } catch {
            print("Encryption error: \(error)")
            return nil
        }
    }
    
    func decryptData(encryptedPackage: [String: String]) -> Data? {
        guard let sessionKey = sessionKey,
              let nonceBase64 = encryptedPackage["nonce"],
              let ciphertextBase64 = encryptedPackage["ciphertext"],
              let nonceData = Data(base64Encoded: nonceBase64),
              let combinedData = Data(base64Encoded: ciphertextBase64) else {
            print("Missing session key or invalid encrypted package")
            return nil
        }
        
        guard combinedData.count > 16 else {
            print("Invalid ciphertext length")
            return nil
        }
        
        let ciphertext = combinedData.prefix(combinedData.count - 16)
        let tag = combinedData.suffix(16)
        
        do {
            let nonce = try AES.GCM.Nonce(data: nonceData)
            let sealedBox = try AES.GCM.SealedBox(nonce: nonce, ciphertext: ciphertext, tag: tag)
            let decryptedData = try AES.GCM.open(sealedBox, using: sessionKey)
            
            return decryptedData
        } catch {
            print("Decryption error: \(error)")
            return nil
        }
    }
    
    func encryptRequest(_ request: [String: Any]) -> [String: String]? {
        guard let jsonData = try? JSONSerialization.data(withJSONObject: request) else {
            print("Failed to serialize request to JSON")
            return nil
        }
        return encryptData(jsonData)
    }
    
    func decryptResponse(encryptedPackage: [String: String]) -> [String: Any]? {
        guard let decryptedData = decryptData(encryptedPackage: encryptedPackage) else {
            return nil
        }
        
        guard let json = try? JSONSerialization.jsonObject(with: decryptedData) as? [String: Any] else {
            print("Failed to parse decrypted data as JSON")
            return nil
        }
        return json
    }
    
    func hasSessionKey() -> Bool {
        return sessionKey != nil
    }
    
    func clearSession() {
        sessionKey = nil
        print("Session key cleared")
    }
}

extension String {
    func chunked(into size: Int) -> [String] {
        var chunks: [String] = []
        var index = startIndex
        
        while index < endIndex {
            let endIdx = self.index(index, offsetBy: size, limitedBy: endIndex) ?? endIndex
            chunks.append(String(self[index..<endIdx]))
            index = endIdx
        }
        
        return chunks
    }
}
