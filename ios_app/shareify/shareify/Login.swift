//
//  Login.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 27..
//

import SwiftUI

struct Login: View {
    @State private var isFlickering = false
    @State private var username: String = ""
    @State private var password: String = ""
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var navigateToHome = false
    @State private var navigateToServerLogin = false
    @State private var showAppLoad = true
    @State private var loginCardOpacity: Double = 0
    @State private var loginCardOffset: CGFloat = 50
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    var body: some View {
        if showAppLoad {
            AppLoad()
                .onAppear {
                    startAppLoadSequence()
                }
        } else if navigateToHome {
            Home()
        } else if navigateToServerLogin {
            ServerLogin()
        } else {
            loginView
                .onAppear {
                    startLoginAnimation()
                }
        }
    }
    
    private var loginView: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {     
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
                  .opacity(loginCardOpacity)
                  .offset(y: loginCardOffset)
                  .ignoresSafeArea(.all, edges: [.bottom, .leading, .trailing])
                  .overlay(
                    GeometryReader { containerGeometry in
                        VStack(spacing: 0) {
                            Spacer()
                            
                            VStack(spacing: min(containerGeometry.size.height * 0.04, 30)) {
                                Text("Welcome Back")
                                    .font(.system(size: min(containerGeometry.size.width * 0.08, 32), weight: .bold))
                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                
                                Text("Sign in to your account")
                                    .font(.system(size: min(containerGeometry.size.width * 0.045, 18), weight: .medium))
                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                
                                VStack(spacing: min(containerGeometry.size.height * 0.02, 16)) {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Email")
                                            .font(.system(size: min(containerGeometry.size.width * 0.04, 16), weight: .medium))
                                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        
                                        TextField("Enter your email", text: $username)
                                            .textFieldStyle(CustomTextFieldStyle())
                                            .frame(height: 50)
                                    }
                                    
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Password")
                                            .font(.system(size: min(containerGeometry.size.width * 0.04, 16), weight: .medium))
                                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        
                                        SecureField("Enter your password", text: $password)
                                            .textFieldStyle(CustomTextFieldStyle())
                                            .frame(height: 50)
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
                                    
                                    Button(action: {
                                        loginAction()
                                    }) {
                                        HStack {
                                            if isLoading {
                                                ProgressView()
                                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                                    .scaleEffect(0.8)
                                            } else {
                                                Text("Sign In")
                                                    .font(.system(size: min(containerGeometry.size.width * 0.045, 18), weight: .semibold))
                                                    .foregroundColor(.white)
                                            }
                                        }
                                        .frame(maxWidth: .infinity)
                                        .frame(height: 55)
                                        .background(
                                            RoundedRectangle(cornerRadius: 15)
                                                .fill(
                                                    LinearGradient(
                                                        gradient: Gradient(colors: [
                                                            Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255),
                                                            Color(red: 0x29/255, green: 0x6D/255, blue: 0xE0/255)
                                                        ]),
                                                        startPoint: .topLeading,
                                                        endPoint: .bottomTrailing
                                                    )
                                                )
                                        )
                                    }
                                    .disabled(isLoading || username.isEmpty || password.isEmpty)
                                    .opacity((username.isEmpty || password.isEmpty) ? 0.6 : 1.0)
                                    .animation(.easeInOut(duration: 0.3), value: username.isEmpty || password.isEmpty)
                                    .padding(.top, min(containerGeometry.size.height * 0.02, 10))
                                }
                                .padding(.horizontal, min(containerGeometry.size.width * 0.08, 30))
                            }
                            
                            Spacer()
                            Spacer()
                        }
                        .padding(.horizontal, min(containerGeometry.size.width * 0.05, 20))
                    }
                  )
            }
        }
        .background(
            GeometryReader { geometry in
                AsyncImage(url: URL(string: backgroundManager.backgroundURL)) { image in
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: geometry.size.height * (1533/862), height: geometry.size.height)
                        .offset(x: -geometry.size.height * (1533/862) * 0.274)
                        .clipped()
                } placeholder: {
                    Color.black
                }
            }
            .ignoresSafeArea(.all)
        )
    }
    
    private func startLoginAnimation() {
        withAnimation(.easeOut(duration: 0.8)) {
            loginCardOpacity = 1.0
            loginCardOffset = 0
        }
    }
    
    private func startAppLoadSequence() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 3.5) {
            checkExistingToken()
        }
    }
    
    private func checkExistingToken() {
        if let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty {
            if let _ = UserDefaults.standard.string(forKey: "server_username"),
               let _ = UserDefaults.standard.string(forKey: "server_password") {
                withAnimation(.easeInOut(duration: 0.5)) {
                    showAppLoad = false
                    navigateToHome = true
                }
            } else {
                withAnimation(.easeInOut(duration: 0.5)) {
                    showAppLoad = false
                    navigateToServerLogin = true
                }
            }
        } else {
            withAnimation(.easeInOut(duration: 0.5)) {
                showAppLoad = false
            }
        }
    }
    
    private func loginAction() {
        withAnimation(.easeInOut(duration: 0.3)) {
            showError = false
            isLoading = true
        }
        
        performLogin()
    }
    
    private func performLogin() {
        guard let url = URL(string: "https://bridge.bbarni.hackclub.app/login") else {
            handleLoginError("Invalid server URL")
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let loginData = [
            "email": username,
            "password": password
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: loginData)
        } catch {
            handleLoginError("Failed to encode login data")
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    handleLoginError("Network error: \(error.localizedDescription)")
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    handleLoginError("Invalid response")
                    return
                }
                
                if httpResponse.statusCode == 200 {
                    if let data = data,
                       let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let jwtToken = json["jwt_token"] as? String {
                        UserDefaults.standard.set(jwtToken, forKey: "jwt_token")
                        UserDefaults.standard.synchronize()
                    }
                    
                    withAnimation(.easeInOut(duration: 0.3)) {
                        isLoading = false
                        navigateToServerLogin = true
                    }
                } else {
                    if let data = data,
                       let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let errorMsg = json["error"] as? String {
                        handleLoginError(errorMsg)
                    } else {
                        handleLoginError("Login failed")
                    }
                }
            }
        }.resume()
    }
    
    private func handleLoginError(_ message: String) {
        withAnimation(.easeInOut(duration: 0.3)) {
            isLoading = false
            showError = true
            errorMessage = message
        }
    }
}

struct CustomTextFieldStyle: TextFieldStyle {
    func _body(configuration: TextField<Self._Label>) -> some View {
        configuration
            .padding(.horizontal, 16)
            .padding(.vertical, 14)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.white.opacity(0.9))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color(red: 0xE5/255, green: 0xE7/255, blue: 0xEB/255), lineWidth: 1.5)
                    )
                    .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
            )
            .font(.system(size: 16, weight: .regular))
            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
    }
}

#Preview {
    Login()
}
