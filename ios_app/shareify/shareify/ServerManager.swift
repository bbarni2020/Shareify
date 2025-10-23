//
//  ServerManager.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 29..
//

import Foundation

class ServerManager: ObservableObject {
    static let shared = ServerManager()
    private var cryptoManager: CryptoManager?
    private var sessionEstablished = false
    
    private init() {
        let clientId = UserDefaults.standard.string(forKey: "client_id") ?? UUID().uuidString
        UserDefaults.standard.set(clientId, forKey: "client_id")
        self.cryptoManager = CryptoManager(clientId: clientId)
    }
    
    func establishEncryptedSession(completion: @escaping (Bool) -> Void) {
        guard let publicKeyPEM = cryptoManager?.getPublicKeyPEM(),
              let jwtToken = UserDefaults.standard.string(forKey: "jwt_token") else {
            print("[Encryption] Missing public key or JWT token")
            completion(false)
            return
        }
        
        guard let url = URL(string: "https://bridge.bbarni.hackclub.app/cloud/establish_session") else {
            completion(false)
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        
        let clientId = UserDefaults.standard.string(forKey: "client_id") ?? ""
        let requestBody: [String: Any] = [
            "client_id": clientId,
            "public_key": publicKeyPEM
        ]
        
        request.httpBody = try? JSONSerialization.data(withJSONObject: requestBody)
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            guard let self = self else {
                completion(false)
                return
            }
            
            if let error = error {
                print("[Encryption] Session establishment error: \(error)")
                completion(false)
                return
            }
            
            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let encryptedKey = json["encrypted_session_key"] as? String else {
                print("[Encryption] Invalid response from server")
                completion(false)
                return
            }
            
            if self.cryptoManager?.decryptSessionKey(encryptedKeyBase64: encryptedKey) == true {
                self.sessionEstablished = true
                print("[Encryption] E2E encryption established successfully")
                completion(true)
            } else {
                print("[Encryption] Failed to decrypt session key")
                completion(false)
            }
        }.resume()
    }
    
    func executeServerCommand(command: String, method: String = "GET", body: [String: Any] = [:], waitTime: Int = 2, completion: @escaping (Result<Any, Error>) -> Void) {
        executeServerCommand(command: command, method: method, body: body, waitTime: waitTime, useEncryption: true, completion: completion)
    }
    
    func executeServerCommand(command: String, method: String = "GET", body: [String: Any] = [:], waitTime: Int = 2, useEncryption: Bool = true, completion: @escaping (Result<Any, Error>) -> Void) {
        
        if useEncryption && !sessionEstablished {
            establishEncryptedSession { [weak self] success in
                if success {
                    self?.executeServerCommand(command: command, method: method, body: body, waitTime: waitTime, useEncryption: useEncryption, completion: completion)
                } else {
                    print("[Encryption] Failed to establish session, falling back to unencrypted")
                    self?.executeServerCommand(command: command, method: method, body: body, waitTime: waitTime, useEncryption: false, completion: completion)
                }
            }
            return
        }
        
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            completion(.failure(ServerError.noJWTToken))
            return
        }
        
        guard let url = URL(string: "https://command.bbarni.hackclub.app/") else {
            completion(.failure(ServerError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")

        if let shareifyJWT = UserDefaults.standard.string(forKey: "shareify_jwt"), !shareifyJWT.isEmpty {
            request.setValue(shareifyJWT, forHTTPHeaderField: "X-Shareify-JWT")
        }

        var requestBody: [String: Any] = [
            "command": command,
            "method": method,
            "wait_time": waitTime
        ]

        if !body.isEmpty {
            requestBody["body"] = body
        }
        
        let clientId = UserDefaults.standard.string(forKey: "client_id") ?? ""
        
        if useEncryption, let encryptedPayload = cryptoManager?.encryptRequest(requestBody) {
            requestBody = [
                "encrypted": true,
                "client_id": clientId,
                "encrypted_payload": encryptedPayload
            ]
            print("[Encryption] Sending encrypted command")
        } else if useEncryption {
            print("[Encryption] Failed to encrypt, sending unencrypted")
        }

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            DispatchQueue.main.async {
                guard let self = self else { return }
                
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    completion(.failure(ServerError.invalidResponse))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(ServerError.noData))
                    return
                }

                if String(data: data, encoding: .utf8) != nil {
                    print("[ServerManager] command=\(command) status=\(httpResponse.statusCode)")
                }
                
                if httpResponse.statusCode == 401 {
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let errorMessage = json["error"] as? String,
                       errorMessage == "Invalid or expired JWT token" {
                        self.refreshJWTTokenAndRetry(originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, useEncryption: useEncryption, completion: completion)
                        return
                    }
                }
                
                do {
                    let json = try JSONSerialization.jsonObject(with: data)
                    
                    if let jsonDict = json as? [String: Any] {
                        if useEncryption, let encrypted = jsonDict["encrypted"] as? Bool, encrypted,
                           let encryptedResponse = jsonDict["encrypted_response"] as? [String: String],
                           let decryptedJson = self.cryptoManager?.decryptResponse(encryptedPackage: encryptedResponse) {
                            print("[Encryption] Received and decrypted response")
                            completion(.success(decryptedJson))
                            return
                        }
                        
                        if let errorMessage = jsonDict["error"] as? String {
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, useEncryption: useEncryption, completion: completion)
                            return
                        }
                        
                        if let success = jsonDict["success"] as? Bool, !success {
                            let errorMessage = jsonDict["error"] as? String ?? "Unknown server error"
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, useEncryption: useEncryption, completion: completion)
                            return
                        }
                        
                        if httpResponse.statusCode == 200 {
                            completion(.success(jsonDict))
                        } else {
                            let errorMessage = jsonDict["error"] as? String ?? "Unknown server error"
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, useEncryption: useEncryption, completion: completion)
                        }
                    } else if json is [Any] {
                        if httpResponse.statusCode == 200 {
                            completion(.success(json))
                        } else {
                            self.handleServerError(errorMessage: "HTTP \(httpResponse.statusCode)", originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, useEncryption: useEncryption, completion: completion)
                        }
                    } else {
                        completion(.failure(ServerError.invalidJSONResponse))
                    }
                } catch {
                    completion(.failure(error))
                }
            }
        }.resume()
    }
    
    private func handleServerError(errorMessage: String, originalCommand: String, originalMethod: String, originalBody: [String: Any], originalWaitTime: Int = 2, useEncryption: Bool = true, completion: @escaping (Result<Any, Error>) -> Void) {
        let isAuthError = errorMessage.lowercased().contains("unauthorized") || 
                         errorMessage.lowercased().contains("token") || 
                         errorMessage.lowercased().contains("auth") || 
                         errorMessage == "Unauthorized" || 
                         errorMessage == "Invalid token"
        
        if isAuthError {
            if let username = UserDefaults.standard.string(forKey: "server_username"),
               let password = UserDefaults.standard.string(forKey: "server_password"),
               !username.isEmpty, !password.isEmpty {
                
                loginToServer(username: username, password: password) { result in
                    switch result {
                    case .success(_):
                        self.executeServerCommand(command: originalCommand, method: originalMethod, body: originalBody, waitTime: originalWaitTime, useEncryption: useEncryption, completion: completion)
                    case .failure(let error):
                        if let serverError = error as? ServerError,
                           case .serverError(let message) = serverError,
                           message.lowercased().contains("unauthorized") {
                            NotificationCenter.default.post(name: NSNotification.Name("RedirectToLogin"), object: nil)
                        } else {
                            NotificationCenter.default.post(name: NSNotification.Name("ShowServerError"), object: nil)
                        }
                        completion(.failure(error))
                    }
                }
            } else {
                completion(.failure(ServerError.serverError(errorMessage)))
            }
        } else {
            NotificationCenter.default.post(name: NSNotification.Name("ShowServerError"), object: nil)
            completion(.failure(ServerError.serverError(errorMessage)))
        }
    }
    
    func loginToServer(username: String, password: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            completion(.failure(ServerError.noJWTToken))
            return
        }
        
        guard let url = URL(string: "https://command.bbarni.hackclub.app/") else {
            completion(.failure(ServerError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        
        let requestBody: [String: Any] = [
            "command": "/user/login",
            "method": "POST",
            "wait_time": 5,
            "body": [
                "username": username,
                "password": password
            ]
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    completion(.failure(error))
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    completion(.failure(ServerError.invalidResponse))
                    return
                }
                
                guard let data = data else {
                    completion(.failure(ServerError.noData))
                    return
                }

                if let raw = String(data: data, encoding: .utf8) {
                    print("[ServerManager] /user/login response status=\(httpResponse.statusCode) -> \(raw)")
                }
                
                do {
                    let json = try JSONSerialization.jsonObject(with: data)
                    
                    if let jsonDict = json as? [String: Any] {
                        if let errorMessage = jsonDict["error"] as? String {
                            completion(.failure(ServerError.serverError(errorMessage)))
                            return
                        }
                        
                        if httpResponse.statusCode == 200 {
                            if let token = jsonDict["token"] as? String {
                                UserDefaults.standard.set(token, forKey: "shareify_jwt")
                                UserDefaults.standard.synchronize()
                            }
                            completion(.success(jsonDict))
                        } else {
                            let errorMessage = jsonDict["error"] as? String ?? "Login failed"
                            completion(.failure(ServerError.serverError(errorMessage)))
                        }
                    } else {
                        completion(.failure(ServerError.invalidJSONResponse))
                    }
                } catch {
                    completion(.failure(error))
                }
            }
        }.resume()
    }
    
    private func refreshJWTTokenAndRetry(originalCommand: String, originalMethod: String, originalBody: [String: Any], originalWaitTime: Int = 2, useEncryption: Bool = true, completion: @escaping (Result<Any, Error>) -> Void) {
        guard let email = UserDefaults.standard.string(forKey: "user_email"),
              let password = UserDefaults.standard.string(forKey: "user_password"),
              !email.isEmpty, !password.isEmpty else {
            completion(.failure(ServerError.serverError("Login credentials not available")))
            return
        }
        
        guard let url = URL(string: "https://bridge.bbarni.hackclub.app/login") else {
            completion(.failure(ServerError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody: [String: Any] = [
            "email": email,
            "password": password
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                guard let data = data,
                      let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode == 200,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let newJwtToken = json["jwt_token"] as? String else {
                    completion(.failure(ServerError.serverError("Failed to refresh login")))
                    return
                }

                if String(data: data, encoding: .utf8) != nil {
                    print("[ServerManager] bridge login refresh -> success")
                }
                
                UserDefaults.standard.set(newJwtToken, forKey: "jwt_token")
                UserDefaults.standard.synchronize()
                
                self.sessionEstablished = false
                
                self.executeServerCommand(command: originalCommand, method: originalMethod, body: originalBody, waitTime: originalWaitTime, useEncryption: useEncryption, completion: completion)
            }
        }.resume()
    }
}

enum ServerError: LocalizedError {
    case noJWTToken
    case invalidURL
    case invalidResponse
    case noData
    case invalidJSONResponse
    case serverError(String)
    case encryptionSetupFailed
    
    var errorDescription: String? {
        switch self {
        case .noJWTToken:
            return "JWT token not found"
        case .invalidURL:
            return "Invalid server URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .noData:
            return "No data received from server"
        case .invalidJSONResponse:
            return "Invalid JSON response"
        case .serverError(let message):
            return message
        case .encryptionSetupFailed:
            return "Failed to establish encrypted connection"
        }
    }
}
