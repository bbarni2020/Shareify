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
        
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            completion(.failure(ServerError.noJWTToken))
            return
        }
        
        guard let url = URL(string: "http://localhost:5698/cloud") else {
            completion(.failure(ServerError.invalidURL))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        
        let requestBody = [
            "command": command,
            "method": method,
            "body": body
        ] as [String : Any]
        
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
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        if httpResponse.statusCode == 200 {
                            completion(.success(json))
                        } else {
                            let errorMessage = json["error"] as? String ?? "Unknown server error"
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
    
    func loginToServer(username: String, password: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let loginBody = [
            "username": username,
            "password": password
        ]
        
        executeServerCommand(command: "/login", method: "POST", body: loginBody, completion: completion)
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
