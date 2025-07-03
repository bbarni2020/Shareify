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
    
    func executeServerCommand(command: String, method: String = "GET", body: [String: Any] = [:], completion: @escaping (Result<[String: Any], Error>) -> Void) {
        
        print("ServerManager: Executing command: \(command) with method: \(method)")
        print("ServerManager: Request body: \(body)")
        
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            print("ServerManager: JWT token not found in UserDefaults")
            completion(.failure(ServerError.noJWTToken))
            return
        }
        
        print("ServerManager: JWT token found: \(jwtToken.prefix(20))...")
        
        guard let url = URL(string: "http://localhost:25841/") else {
            print("ServerManager: Invalid URL")
            completion(.failure(ServerError.invalidURL))
            return
        }
        
        print("ServerManager: Making request to: \(url.absoluteString)")
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        
        if let shareifyJWT = UserDefaults.standard.string(forKey: "shareify_jwt"), !shareifyJWT.isEmpty {
            print("ServerManager: Adding X-Shareify-JWT header: \(shareifyJWT.prefix(20))...")
            request.setValue(shareifyJWT, forHTTPHeaderField: "X-Shareify-JWT")
        } else {
            print("ServerManager: No Shareify JWT found in UserDefaults")
        }
        
        var requestBody: [String: Any] = [
            "command": command,
            "method": method,
            "wait_time": 2
        ]
        
        if !body.isEmpty {
            requestBody["body"] = body
        }
        
        print("ServerManager: Full request body: \(requestBody)")
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
            print("ServerManager: Request body serialized successfully")
        } catch {
            print("ServerManager: Failed to serialize request body: \(error.localizedDescription)")
            completion(.failure(error))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                print("ServerManager: Request completed for command: \(command)")
                
                if let error = error {
                    print("ServerManager: Network error occurred: \(error.localizedDescription)")
                    completion(.failure(error))
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    print("ServerManager: Invalid HTTP response received")
                    completion(.failure(ServerError.invalidResponse))
                    return
                }
                
                print("ServerManager: HTTP Status Code: \(httpResponse.statusCode)")
                
                guard let data = data else {
                    print("ServerManager: No data received from server")
                    completion(.failure(ServerError.noData))
                    return
                }
                
                print("ServerManager: Received data length: \(data.count) bytes")
                
                if let responseString = String(data: data, encoding: .utf8) {
                    print("ServerManager: Raw cloud response: \(responseString)")
                } else {
                    print("ServerManager: Unable to convert response data to string")
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        print("ServerManager: Parsed JSON response: \(json)")
                        
                        if let success = json["success"] as? Bool, !success {
                            let errorMessage = json["error"] as? String ?? "Unknown server error"
                            let timestamp = json["timestamp"] as? String ?? "Unknown time"
                            print("ServerManager: Server returned error - Message: \(errorMessage), Timestamp: \(timestamp)")
                            completion(.failure(ServerError.serverError(errorMessage)))
                            return
                        }
                        
                        if httpResponse.statusCode == 200 {
                            print("ServerManager: Request successful, returning response")
                            completion(.success(json))
                        } else {
                            let errorMessage = json["error"] as? String ?? "Unknown server error"
                            print("ServerManager: HTTP error \(httpResponse.statusCode): \(errorMessage)")
                            completion(.failure(ServerError.serverError(errorMessage)))
                        }
                    } else {
                        print("ServerManager: Failed to parse JSON response")
                        completion(.failure(ServerError.invalidJSONResponse))
                    }
                } catch {
                    print("ServerManager: JSON parsing error: \(error.localizedDescription)")
                    completion(.failure(error))
                }
            }
        }.resume()
    }
    
    func loginToServer(username: String, password: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        print("ServerManager: Starting login process for user: \(username)")
        
        let loginBody = [
            "username": username,
            "password": password
        ]
        
        print("ServerManager: Login body prepared: \(loginBody)")
        
        executeServerCommand(command: "/user/login", method: "POST", body: loginBody) { result in
            switch result {
            case .success(let response):
                print("ServerManager: Login successful, response: \(response)")
                
                if let token = response["token"] as? String {
                    print("ServerManager: JWT token received: \(token.prefix(20))...")
                    UserDefaults.standard.set(token, forKey: "shareify_jwt")
                    UserDefaults.standard.synchronize()
                    print("ServerManager: JWT token saved to UserDefaults")
                } else {
                    print("ServerManager: Warning - No token found in successful response")
                }
                
                completion(.success(response))
                
            case .failure(let error):
                print("ServerManager: Login failed with error: \(error.localizedDescription)")
                completion(.failure(error))
            }
        }
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
