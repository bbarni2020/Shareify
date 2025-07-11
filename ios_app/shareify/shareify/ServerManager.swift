//
//  ServerManager.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 29..
//

import Foundation

class ServerManager: ObservableObject {
    static let shared = ServerManager()
    
    private init() {}
    
    func executeServerCommand(command: String, method: String = "GET", body: [String: Any] = [:], waitTime: Int = 2, completion: @escaping (Result<Any, Error>) -> Void) {
        
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
                
                if httpResponse.statusCode == 401 {
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let errorMessage = json["error"] as? String,
                       errorMessage == "Invalid or expired JWT token" {
                        self.refreshJWTTokenAndRetry(originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, completion: completion)
                        return
                    }
                }
                
                do {
                    let json = try JSONSerialization.jsonObject(with: data)
                    
                    if let jsonDict = json as? [String: Any] {
                        if let errorMessage = jsonDict["error"] as? String {
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, completion: completion)
                            return
                        }
                        
                        if let success = jsonDict["success"] as? Bool, !success {
                            let errorMessage = jsonDict["error"] as? String ?? "Unknown server error"
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, completion: completion)
                            return
                        }
                        
                        if httpResponse.statusCode == 200 {
                            completion(.success(jsonDict))
                        } else {
                            let errorMessage = jsonDict["error"] as? String ?? "Unknown server error"
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, completion: completion)
                        }
                    } else if json is [Any] {
                        if httpResponse.statusCode == 200 {
                            completion(.success(json))
                        } else {
                            self.handleServerError(errorMessage: "HTTP \(httpResponse.statusCode)", originalCommand: command, originalMethod: method, originalBody: body, originalWaitTime: waitTime, completion: completion)
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
    
    private func handleServerError(errorMessage: String, originalCommand: String, originalMethod: String, originalBody: [String: Any], originalWaitTime: Int = 2, completion: @escaping (Result<Any, Error>) -> Void) {
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
                        self.executeServerCommand(command: originalCommand, method: originalMethod, body: originalBody, waitTime: originalWaitTime, completion: completion)
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
    
    private func refreshJWTTokenAndRetry(originalCommand: String, originalMethod: String, originalBody: [String: Any], originalWaitTime: Int = 2, completion: @escaping (Result<Any, Error>) -> Void) {
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
                
                UserDefaults.standard.set(newJwtToken, forKey: "jwt_token")
                UserDefaults.standard.synchronize()
                
                self.executeServerCommand(command: originalCommand, method: originalMethod, body: originalBody, waitTime: originalWaitTime, completion: completion)
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
        }
    }
}
