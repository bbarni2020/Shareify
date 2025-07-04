//
//  ServerLogin.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 29..
//

import SwiftUI

struct ServerLogin: View {
    @State private var serverUsername: String = ""
    @State private var serverPassword: String = ""
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""
    @State private var navigateToHome = false
    @State private var loginCardOpacity: Double = 0
    @State private var loginCardOffset: CGFloat = 50
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    var body: some View {
        if navigateToHome {
            Home()
        } else {
            serverLoginView
                .onAppear {
                    startLoginAnimation()
                    loadSavedCredentials()
                }
        }
    }
    
    private var serverLoginView: some View {
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
                                Text("Server Login")
                                    .font(.system(size: min(containerGeometry.size.width * 0.08, 32), weight: .bold))
                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                
                                Text("Connect to your Shareify server")
                                    .font(.system(size: min(containerGeometry.size.width * 0.045, 18), weight: .medium))
                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                
                                VStack(spacing: min(containerGeometry.size.height * 0.02, 16)) {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Server Username")
                                            .font(.system(size: min(containerGeometry.size.width * 0.04, 16), weight: .medium))
                                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        
                                        TextField("Enter server username", text: $serverUsername)
                                            .textFieldStyle(CustomTextFieldStyle())
                                            .frame(height: 50)
                                    }
                                    
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text("Server Password")
                                            .font(.system(size: min(containerGeometry.size.width * 0.04, 16), weight: .medium))
                                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        
                                        SecureField("Enter server password", text: $serverPassword)
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
                                        serverLoginAction()
                                    }) {
                                        HStack {
                                            if isLoading {
                                                ProgressView()
                                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                                    .scaleEffect(0.8)
                                            } else {
                                                Text("Connect to Server")
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
                                    .disabled(isLoading || serverUsername.isEmpty || serverPassword.isEmpty)
                                    .opacity((serverUsername.isEmpty || serverPassword.isEmpty) ? 0.6 : 1.0)
                                    .animation(.easeInOut(duration: 0.3), value: serverUsername.isEmpty || serverPassword.isEmpty)
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
    
    private func loadSavedCredentials() {
        if let savedUsername = UserDefaults.standard.string(forKey: "server_username") {
            serverUsername = savedUsername
        }
        if let savedPassword = UserDefaults.standard.string(forKey: "server_password") {
            serverPassword = savedPassword
        }
    }
    
    private func serverLoginAction() {
        withAnimation(.easeInOut(duration: 0.3)) {
            showError = false
            isLoading = true
        }
        
        performServerLogin()
    }
    
    private func performServerLogin() {
        ServerManager.shared.loginToServer(username: serverUsername, password: serverPassword) { result in
            switch result {
            case .success(_):
                UserDefaults.standard.set(self.serverUsername, forKey: "server_username")
                UserDefaults.standard.set(self.serverPassword, forKey: "server_password")
                UserDefaults.standard.synchronize()
                
                withAnimation(.easeInOut(duration: 0.3)) {
                    self.isLoading = false
                    self.navigateToHome = true
                }
            case .failure(let error):
                self.handleServerLoginError(error.localizedDescription)
            }
        }
    }
    
    private func skipServerLogin() {
        withAnimation(.easeInOut(duration: 0.3)) {
            navigateToHome = true
        }
    }
    
    private func handleServerLoginError(_ message: String) {
        withAnimation(.easeInOut(duration: 0.3)) {
            isLoading = false
            showError = true
            errorMessage = message
        }
    }
}

#Preview {
    ServerLogin()
}
