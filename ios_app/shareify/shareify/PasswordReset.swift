//
//  PasswordReset.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 07. 04..
//

import SwiftUI

struct PasswordReset: View {
    let isCloudAccount: Bool
    @State private var currentPassword: String = ""
    @State private var newPassword: String = ""
    @State private var confirmPassword: String = ""
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var showSuccess = false
    @State private var successMessage = ""
    @StateObject private var backgroundManager = BackgroundManager.shared
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                HStack(alignment: .center, spacing: 10) {
                    Button(action: {
                        let impactFeedback = UIImpactFeedbackGenerator(style: .light)
                        impactFeedback.impactOccurred()
                        dismiss()
                    }) {
                        Rectangle()
                            .foregroundColor(.clear)
                            .frame(width: 50, height: 50)
                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                            .overlay(
                                Image(systemName: "chevron.left")
                                    .font(.system(size: 18, weight: .medium))
                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                            )
                    }
                    
                    Rectangle()
                        .foregroundColor(.clear)
                        .frame(width: 238 * (50 / 62), height: 50)
                        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                        .overlay(
                            Text(isCloudAccount ? "Cloud Password" : "Local Password")
                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                .font(.system(size: 16, weight: .medium))
                        )
                    
                    Spacer()
                }
                .padding(.horizontal, 20)
                .padding(.top, 5)
                
                Spacer(minLength: 35)
                
                Rectangle()
                    .foregroundColor(.clear)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(.ultraThinMaterial, in: UnevenRoundedRectangle(
                        topLeadingRadius: 40,
                        bottomLeadingRadius: 0,
                        bottomTrailingRadius: 0,
                        topTrailingRadius: 40
                    ))
                    .shadow(color: .white.opacity(0.25), radius: 2.5, x: 0, y: 4)
                    .ignoresSafeArea(.all, edges: [.bottom, .leading, .trailing])
                    .overlay(
                        VStack(spacing: 0) {
                            Spacer()
                            
                            VStack(spacing: 30) {
                                Text("Change \(isCloudAccount ? "Cloud" : "Local") Password")
                                    .font(.system(size: 28, weight: .bold))
                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                
                                Text("Enter your \(isCloudAccount ? "current password and " : "")new password")
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                
                                VStack(spacing: 16) {
                                    if isCloudAccount {
                                        VStack(alignment: .leading, spacing: 8) {
                                            Text("Current Password")
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                            
                                            SecureField("Enter current password", text: $currentPassword)
                                                .padding(.horizontal, 15)
                                                .padding(.vertical, 12)
                                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 20)
                                                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                                )
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                        }
                                    }
                                    
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("New Password")
                                            .font(.system(size: 16, weight: .medium))
                                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        
                                        SecureField("Enter new password", text: $newPassword)
                                            .padding(.horizontal, 15)
                                            .padding(.vertical, 12)
                                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 20)
                                                    .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                            )
                                            .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                    }
                                    
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Confirm Password")
                                            .font(.system(size: 16, weight: .medium))
                                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        
                                        SecureField("Confirm new password", text: $confirmPassword)
                                            .padding(.horizontal, 15)
                                            .padding(.vertical, 12)
                                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                                            .overlay(
                                                RoundedRectangle(cornerRadius: 20)
                                                    .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                            )
                                            .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                    }
                                    
                                    if showError {
                                        HStack {
                                            Image(systemName: "exclamationmark.triangle.fill")
                                                .foregroundColor(Color.red)
                                                .font(.system(size: 14))
                                            Text(errorMessage)
                                                .font(.system(size: 14, weight: .medium))
                                                .foregroundColor(Color.red)
                                            Spacer()
                                        }
                                        .padding(.top, 5)
                                        .transition(.opacity.combined(with: .move(edge: .top)))
                                    }
                                    
                                    if showSuccess {
                                        HStack {
                                            Image(systemName: "checkmark.circle.fill")
                                                .foregroundColor(Color.green)
                                                .font(.system(size: 14))
                                            Text(successMessage)
                                                .font(.system(size: 14, weight: .medium))
                                                .foregroundColor(Color.green)
                                            Spacer()
                                        }
                                        .padding(.top, 5)
                                        .transition(.opacity.combined(with: .move(edge: .top)))
                                    }
                                    
                                    Button(action: changePassword) {
                                        HStack {
                                            if isLoading {
                                                ProgressView()
                                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                                    .scaleEffect(0.8)
                                            } else {
                                                Text("Change Password")
                                                    .font(.system(size: 18, weight: .semibold))
                                                    .foregroundColor(.white)
                                            }
                                        }
                                        .frame(maxWidth: .infinity)
                                        .frame(height: 55)
                                        .background(
                                            RoundedRectangle(cornerRadius: 25)
                                                .fill(
                                                    LinearGradient(
                                                        gradient: Gradient(colors: [
                                                            isCloudAccount ? Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255) : Color(red: 0x65/255, green: 0xdc/255, blue: 0x50/255),
                                                            isCloudAccount ? Color(red: 0x2d/255, green: 0x6b/255, blue: 0xdb/255) : Color(red: 0x4a/255, green: 0xc1/255, blue: 0x3a/255)
                                                        ]),
                                                        startPoint: .topLeading,
                                                        endPoint: .bottomTrailing
                                                    )
                                                )
                                        )
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 25)
                                                .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                        )
                                        .shadow(color: (isCloudAccount ? Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255) : Color(red: 0x65/255, green: 0xdc/255, blue: 0x50/255)).opacity(0.3), radius: 8, x: 0, y: 4)
                                    }
                                    .disabled(isLoading || (isCloudAccount && currentPassword.isEmpty) || newPassword.isEmpty || confirmPassword.isEmpty)
                                    .opacity(((isCloudAccount && currentPassword.isEmpty) || newPassword.isEmpty || confirmPassword.isEmpty) ? 0.6 : 1.0)
                                    .animation(.easeInOut(duration: 0.3), value: (isCloudAccount && currentPassword.isEmpty) || newPassword.isEmpty || confirmPassword.isEmpty)
                                    .padding(.top, 10)
                                }
                                .padding(.horizontal, 30)
                            }
                            
                            Spacer()
                            Spacer()
                        }
                        .padding(.horizontal, 20)
                    )
            }
        }
        .background(
            GeometryReader { geometry in
                Image(backgroundManager.backgroundImageName)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: geometry.size.height * (1533/862), height: geometry.size.height)
                    .offset(x: -geometry.size.height * (1533/862) * 0.274)
                    .clipped()
            }
            .ignoresSafeArea(.all)
        )
    }
    
    private func changePassword() {
        guard newPassword == confirmPassword else {
            showError(message: "Passwords do not match")
            return
        }
        
        guard newPassword.count >= 6 else {
            showError(message: "Password must be at least 6 characters")
            return
        }
        
        guard !currentPassword.isEmpty else {
            showError(message: "Current password is required")
            return
        }
        
        withAnimation(.easeInOut(duration: 0.3)) {
            showError = false
            showSuccess = false
            isLoading = true
        }
        
        if isCloudAccount {
            changeCloudPassword()
        } else {
            changeLocalPassword()
        }
    }
    
    private func changeCloudPassword() {
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            showError(message: "Not logged in to cloud account")
            return
        }
        
        guard let url = URL(string: "https://bridge.bbarni.hackclub.app/user/change-password") else {
            showError(message: "Invalid server URL")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody: [String: Any] = [
            "current_password": currentPassword,
            "new_password": newPassword
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            showError(message: "Failed to create request")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isLoading = false
                
                if let error = error {
                    self.showError(message: "Network error: \(error.localizedDescription)")
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    self.showError(message: "Invalid response")
                    return
                }
                
                guard let data = data else {
                    self.showError(message: "No response data")
                    return
                }
                
                if httpResponse.statusCode == 401 {
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let errorMessage = json["error"] as? String,
                       errorMessage == "Invalid or expired JWT token" {
                        self.refreshJWTTokenAndRetry {
                            self.changeCloudPassword()
                        }
                        return
                    }
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        if httpResponse.statusCode == 200 {
                            if let message = json["message"] as? String {
                                UserDefaults.standard.set(self.newPassword, forKey: "user_password")
                                UserDefaults.standard.synchronize()
                                self.showSuccess(message: message)
                                self.clearFields()
                            } else {
                                UserDefaults.standard.set(self.newPassword, forKey: "user_password")
                                UserDefaults.standard.synchronize()
                                self.showSuccess(message: "Password changed successfully")
                                self.clearFields()
                            }
                        } else {
                            if let errorMessage = json["error"] as? String {
                                self.showError(message: errorMessage)
                            } else {
                                self.showError(message: "Password change failed")
                            }
                        }
                    } else {
                        self.showError(message: "Invalid response format")
                    }
                } catch {
                    self.showError(message: "Failed to parse response")
                }
            }
        }.resume()
    }
    
    private func changeLocalPassword() {
        ServerManager.shared.executeServerCommand(
            command: "/user/change_password",
            method: "POST",
            body: [
                "new_password": newPassword
            ]
        ) { result in
            self.isLoading = false
            
            switch result {
            case .success(_):
                UserDefaults.standard.set(self.newPassword, forKey: "server_password")
                UserDefaults.standard.synchronize()
                
                self.showSuccess(message: "Local password updated successfully")
                self.clearFields()
                
            case .failure(let error):
                self.showError(message: error.localizedDescription)
            }
        }
    }
    
    private func showError(message: String) {
        withAnimation(.easeInOut(duration: 0.3)) {
            showSuccess = false
            showError = true
            errorMessage = message
            isLoading = false
        }
    }
    
    private func showSuccess(message: String) {
        withAnimation(.easeInOut(duration: 0.3)) {
            showError = false
            showSuccess = true
            successMessage = message
        }
    }
    
    private func clearFields() {
        currentPassword = ""
        newPassword = ""
        confirmPassword = ""
    }
    
    private func refreshJWTTokenAndRetry(completion: @escaping () -> Void) {
        guard let email = UserDefaults.standard.string(forKey: "user_email"),
              let password = UserDefaults.standard.string(forKey: "user_password"),
              !email.isEmpty, !password.isEmpty else {
            showError(message: "Login credentials not available")
            return
        }
        
        guard let url = URL(string: "https://bridge.bbarni.hackclub.app/login") else {
            showError(message: "Invalid login URL")
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
            showError(message: "Failed to create login request")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                guard let data = data,
                      let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode == 200,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let newJwtToken = json["jwt_token"] as? String else {
                    self.showError(message: "Failed to refresh login")
                    return
                }
                
                UserDefaults.standard.set(newJwtToken, forKey: "jwt_token")
                UserDefaults.standard.synchronize()
                completion()
            }
        }.resume()
    }
}

#Preview {
    PasswordReset(isCloudAccount: true)
}
