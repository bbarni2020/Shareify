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
    
    func executeServerCommand(command: String, method: String = "GET", body: [String: Any] = [:], completion: @escaping (Result<Any, Error>) -> Void) {
        
        print("DEBUG: executeServerCommand called - command: \(command), method: \(method)")
        
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            print("DEBUG: No JWT token found")
            completion(.failure(ServerError.noJWTToken))
            return
        }
        
        guard let url = URL(string: "https://command.bbarni.hackclub.app/") else {
            print("DEBUG: Invalid URL")
            completion(.failure(ServerError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        
        if let shareifyJWT = UserDefaults.standard.string(forKey: "shareify_jwt"), !shareifyJWT.isEmpty {
            print("DEBUG: Adding shareify JWT header")
            request.setValue(shareifyJWT, forHTTPHeaderField: "X-Shareify-JWT")
        } else {
            print("DEBUG: No shareify JWT found")
        }
        
        var requestBody: [String: Any] = [
            "command": command,
            "method": method,
            "wait_time": 2
        ]
        
        if !body.isEmpty {
            requestBody["body"] = body
        }
        
        print("DEBUG: Request body: \(requestBody)")
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            print("DEBUG: Failed to serialize request body: \(error)")
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    print("DEBUG: Network error: \(error)")
                    completion(.failure(error))
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    print("DEBUG: Invalid HTTP response")
                    completion(.failure(ServerError.invalidResponse))
                    return
                }
                
                print("DEBUG: HTTP status code: \(httpResponse.statusCode)")
                
                guard let data = data else {
                    print("DEBUG: No data received")
                    completion(.failure(ServerError.noData))
                    return
                }
                
                if let responseString = String(data: data, encoding: .utf8) {
                    print("DEBUG: Raw response: \(responseString)")
                }
                
                do {
                    let json = try JSONSerialization.jsonObject(with: data)
                    print("DEBUG: Parsed JSON: \(json)")
                    
                    if let jsonDict = json as? [String: Any] {
                        if let errorMessage = jsonDict["error"] as? String {
                            print("DEBUG: Server error detected: \(errorMessage)")
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, completion: completion)
                            return
                        }
                        
                        if let success = jsonDict["success"] as? Bool, !success {
                            let errorMessage = jsonDict["error"] as? String ?? "Unknown server error"
                            print("DEBUG: Server error detected: \(errorMessage)")
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, completion: completion)
                            return
                        }
                        
                        if httpResponse.statusCode == 200 {
                            print("DEBUG: Request successful")
                            completion(.success(jsonDict))
                        } else {
                            let errorMessage = jsonDict["error"] as? String ?? "Unknown server error"
                            print("DEBUG: HTTP error with message: \(errorMessage)")
                            self.handleServerError(errorMessage: errorMessage, originalCommand: command, originalMethod: method, originalBody: body, completion: completion)
                        }
                    } else if json is [Any] {
                        if httpResponse.statusCode == 200 {
                            print("DEBUG: Array response successful")
                            completion(.success(json))
                        } else {
                            print("DEBUG: HTTP error with array response")
                            self.handleServerError(errorMessage: "HTTP \(httpResponse.statusCode)", originalCommand: command, originalMethod: method, originalBody: body, completion: completion)
                        }
                    } else {
                        print("DEBUG: Invalid JSON format")
                        completion(.failure(ServerError.invalidJSONResponse))
                    }
                } catch {
                    print("DEBUG: JSON parsing error: \(error)")
                    completion(.failure(error))
                }
            }
        }.resume()
    }
    
    private func handleServerError(errorMessage: String, originalCommand: String, originalMethod: String, originalBody: [String: Any], completion: @escaping (Result<Any, Error>) -> Void) {
        print("DEBUG: handleServerError called with message: '\(errorMessage)'")
        print("DEBUG: Checking if error is auth-related...")
        
        let isAuthError = errorMessage.lowercased().contains("unauthorized") || 
                         errorMessage.lowercased().contains("token") || 
                         errorMessage.lowercased().contains("auth") || 
                         errorMessage == "Unauthorized" || 
                         errorMessage == "Invalid token"
        
        print("DEBUG: Is auth error: \(isAuthError)")
        
        if isAuthError {
            print("DEBUG: Unauthorized error detected, attempting re-authentication")
            if let username = UserDefaults.standard.string(forKey: "server_username"),
               let password = UserDefaults.standard.string(forKey: "server_password"),
               !username.isEmpty, !password.isEmpty {
                
                print("DEBUG: Found saved credentials, logging in with username: \(username)")
                loginToServer(username: username, password: password) { result in
                    switch result {
                    case .success(_):
                        print("DEBUG: Re-authentication successful, retrying original command: \(originalCommand)")
                        // Retry the original command
                        self.executeServerCommand(command: originalCommand, method: originalMethod, body: originalBody, completion: completion)
                    case .failure(let error):
                        print("DEBUG: Re-authentication failed: \(error)")
                        completion(.failure(ServerError.serverError(errorMessage)))
                    }
                }
            } else {
                print("DEBUG: No saved credentials found")
                completion(.failure(ServerError.serverError(errorMessage)))
            }
        } else {
            print("DEBUG: Non-auth error, passing through: \(errorMessage)")
            completion(.failure(ServerError.serverError(errorMessage)))
        }
    }
    
    func loginToServer(username: String, password: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        print("DEBUG: loginToServer called with username: \(username)")
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            print("DEBUG: No JWT token for login")
            completion(.failure(ServerError.noJWTToken))
            return
        }
        
        guard let url = URL(string: "https://command.bbarni.hackclub.app/") else {
            print("DEBUG: Invalid URL for login")
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
            "wait_time": 2,
            "body": [
                "username": username,
                "password": password
            ]
        ]
        
        print("DEBUG: Login request body: \(requestBody)")
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            print("DEBUG: Failed to serialize login request: \(error)")
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    print("DEBUG: Login network error: \(error)")
                    completion(.failure(error))
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    print("DEBUG: Invalid login HTTP response")
                    completion(.failure(ServerError.invalidResponse))
                    return
                }
                
                print("DEBUG: Login HTTP status: \(httpResponse.statusCode)")
                
                guard let data = data else {
                    print("DEBUG: No login data received")
                    completion(.failure(ServerError.noData))
                    return
                }
                
                if let responseString = String(data: data, encoding: .utf8) {
                    print("DEBUG: Login raw response: \(responseString)")
                }
                
                do {
                    let json = try JSONSerialization.jsonObject(with: data)
                    print("DEBUG: Login parsed JSON: \(json)")
                    
                    if let jsonDict = json as? [String: Any] {
                        if let errorMessage = jsonDict["error"] as? String {
                            print("DEBUG: Login failed with error: \(errorMessage)")
                            completion(.failure(ServerError.serverError(errorMessage)))
                            return
                        }
                        
                        if httpResponse.statusCode == 200 {
                            if let token = jsonDict["token"] as? String {
                                print("DEBUG: Login successful, saving new token")
                                UserDefaults.standard.set(token, forKey: "shareify_jwt")
                                UserDefaults.standard.synchronize()
                            } else {
                                print("DEBUG: Login successful but no token in response")
                            }
                            completion(.success(jsonDict))
                        } else {
                            let errorMessage = jsonDict["error"] as? String ?? "Login failed"
                            print("DEBUG: Login failed with error: \(errorMessage)")
                            completion(.failure(ServerError.serverError(errorMessage)))
                        }
                    } else {
                        print("DEBUG: Invalid login JSON format")
                        completion(.failure(ServerError.invalidJSONResponse))
                    }
                } catch {
                    print("DEBUG: Login JSON parsing error: \(error)")
                    completion(.failure(error))
                }
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
