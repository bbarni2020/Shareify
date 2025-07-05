//
//  Settings.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 07. 03..
//

import SwiftUI

struct Settings: View {
    @State private var email: String = ""
    @State private var username: String = ""
    @State private var localUsername: String = UserDefaults.standard.string(forKey: "server_username") ?? "Loading..."
    @State private var selectedBackground: Int = 1
    @State private var alertMessage = ""
    @State private var navigateToLogin = false
    @State private var navigateToServerLogin = false
    @State private var showingCloudPasswordReset = false
    @State private var showingLocalPasswordReset = false
    @State private var isLoadingCloudData = false
    @State private var isLoadingShareifyData = false
    @StateObject private var backgroundManager = BackgroundManager.shared
    @Environment(\.dismiss) private var dismiss
    
    let backgroundOptions = Array(1...19)
    
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
                            .colorScheme(.light)
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
                        .colorScheme(.light)
                        .overlay(
                            Text("Settings")
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
                    .colorScheme(.light)
                    .shadow(color: .white.opacity(0.25), radius: 2.5, x: 0, y: 4)
                    .ignoresSafeArea(.all, edges: [.bottom, .leading, .trailing])
                    .overlay(
                        ScrollView {
                            VStack(spacing: 30) {
                                VStack(alignment: .leading, spacing: 20) {
                                    HStack {
                                        Text("Cloud Account")
                                            .font(.system(size: 22, weight: .semibold))
                                            .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                        Spacer()
                                    }
                                    
                                    VStack(spacing: 15) {
                                        HStack {
                                            Text("Email:")
                                                .font(.system(size: 14, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .frame(width: 80, alignment: .leading)
                                            if isLoadingCloudData {
                                                ProgressView()
                                                    .scaleEffect(0.8)
                                                    .frame(height: 20)
                                            } else {
                                                Text(email)
                                                    .font(.system(size: 14, weight: .regular))
                                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                            }
                                            Spacer()
                                        }
                                        
                                        HStack {
                                            Text("Username:")
                                                .font(.system(size: 14, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .frame(width: 80, alignment: .leading)
                                            if isLoadingCloudData {
                                                ProgressView()
                                                    .scaleEffect(0.8)
                                                    .frame(height: 20)
                                            } else {
                                                Text(username)
                                                    .font(.system(size: 14, weight: .regular))
                                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                            }
                                            Spacer()
                                        }
                                        
                                        VStack(spacing: 10) {
                                            Button(action: {
                                                showingCloudPasswordReset = true
                                            }) {
                                                Text("Change Password")
                                                    .font(.system(size: 14, weight: .medium))
                                                    .foregroundColor(.white)
                                                    .frame(maxWidth: .infinity)
                                                    .padding(.vertical, 14)
                                                    .background(
                                                        LinearGradient(
                                                            gradient: Gradient(colors: [
                                                                Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255),
                                                                Color(red: 0x2d/255, green: 0x6b/255, blue: 0xdb/255)
                                                            ]),
                                                            startPoint: .topLeading,
                                                            endPoint: .bottomTrailing
                                                        ),
                                                        in: RoundedRectangle(cornerRadius: 25)
                                                    )
                                                    .overlay(
                                                        RoundedRectangle(cornerRadius: 25)
                                                            .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                                    )
                                                    .shadow(color: Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255).opacity(0.3), radius: 8, x: 0, y: 4)
                                            }
                                        
                                        Button(action: logoutCloud) {
                                            Text("Logout Cloud Account")
                                                .font(.system(size: 14, weight: .medium))
                                                .foregroundColor(.white)
                                                .frame(maxWidth: .infinity)
                                                .padding(.vertical, 15)
                                                .background(
                                                    LinearGradient(
                                                        gradient: Gradient(colors: [
                                                            Color.red,
                                                            Color(red: 0.8, green: 0.2, blue: 0.2)
                                                        ]),
                                                        startPoint: .topLeading,
                                                        endPoint: .bottomTrailing
                                                    )
                                                )
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 25)
                                                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                                )
                                                .cornerRadius(25)
                                                .shadow(color: Color.red.opacity(0.3), radius: 8, x: 0, y: 4)
                                        }
                                        }
                                    }
                                }
                                .padding(20)
                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
                                .colorScheme(.light)
                                
                                VStack(alignment: .leading, spacing: 20) {
                                    HStack {
                                        Text("Local Shareify Settings")
                                            .font(.system(size: 22, weight: .semibold))
                                            .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                        Spacer()
                                    }
                                    
                                    VStack(spacing: 15) {
                                        HStack {
                                            Text("Username:")
                                                .font(.system(size: 14, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .frame(width: 80, alignment: .leading)
                                            if isLoadingShareifyData {
                                                ProgressView()
                                                    .scaleEffect(0.8)
                                                    .frame(height: 20)
                                            } else {
                                                Text(localUsername)
                                                    .font(.system(size: 14, weight: .regular))
                                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                            }
                                            Spacer()
                                        }
                                        
                                        VStack(spacing: 10) {
                                            Button(action: {
                                                showingLocalPasswordReset = true
                                            }) {
                                                Text("Change Local Password")
                                                    .font(.system(size: 14, weight: .medium))
                                                    .foregroundColor(.white)
                                                    .frame(maxWidth: .infinity)
                                                    .padding(.vertical, 15)
                                                    .background(
                                                        LinearGradient(
                                                            gradient: Gradient(colors: [
                                                                Color(red: 0x65/255, green: 0xdc/255, blue: 0x50/255),
                                                                Color(red: 0x4a/255, green: 0xc1/255, blue: 0x3a/255)
                                                            ]),
                                                            startPoint: .topLeading,
                                                            endPoint: .bottomTrailing
                                                        )
                                                    )
                                                    .overlay(
                                                        RoundedRectangle(cornerRadius: 25)
                                                            .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                                    )
                                                    .cornerRadius(25)
                                                    .shadow(color: Color(red: 0x65/255, green: 0xdc/255, blue: 0x50/255).opacity(0.3), radius: 8, x: 0, y: 4)
                                            }
                                        }
                                        
                                        VStack(alignment: .leading, spacing: 10) {
                                            Text("Background:")
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                            
                                            ScrollView(.horizontal, showsIndicators: false) {
                                                HStack(spacing: 15) {
                                                    ForEach(backgroundOptions, id: \.self) { backgroundNumber in
                                                        Image("back\(backgroundNumber)")
                                                            .resizable()
                                                            .aspectRatio(contentMode: .fill)
                                                            .frame(width: 80, height: 60)
                                                            .clipped()
                                                            .cornerRadius(15)
                                                            .overlay(
                                                                RoundedRectangle(cornerRadius: 15)
                                                                    .stroke(backgroundManager.selectedBackground == backgroundNumber ? Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255) : Color.clear, lineWidth: 3)
                                                            )
                                                            .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
                                                            .onTapGesture {
                                                                backgroundManager.saveSelectedBackground(backgroundNumber)
                                                            }
                                                    }
                                                }
                                                .padding(.horizontal, 5)
                                            }
                                        }
                                        
                                        Button(action: logoutLocal) {
                                            Text("Logout Local Server")
                                                .font(.system(size: 14, weight: .medium))
                                                .foregroundColor(.white)
                                                .frame(maxWidth: .infinity)
                                                .padding(.vertical, 15)
                                                .background(
                                                    LinearGradient(
                                                        gradient: Gradient(colors: [
                                                            Color.red,
                                                            Color(red: 0.8, green: 0.2, blue: 0.2)
                                                        ]),
                                                        startPoint: .topLeading,
                                                        endPoint: .bottomTrailing
                                                    )
                                                )
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 25)
                                                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                                )
                                                .cornerRadius(25)
                                                .shadow(color: Color.red.opacity(0.3), radius: 8, x: 0, y: 4)
                                        }
                                    }
                                }
                                .padding(20)
                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
                                .colorScheme(.light)
                                
                                VStack(alignment: .leading, spacing: 20) {
                                    HStack {
                                        Text("Links")
                                            .font(.system(size: 22, weight: .semibold))
                                            .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                        Spacer()
                                    }
                                    
                                    Button(action: openGitHubGuides) {
                                        HStack {
                                            Image(systemName: "book.fill")
                                                .font(.system(size: 16))
                                                .foregroundColor(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255))
                                            Text("GitHub Guides")
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255))
                                            Spacer()
                                            Image(systemName: "arrow.up.right")
                                                .font(.system(size: 14))
                                                .foregroundColor(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255))
                                        }
                                        .padding(.vertical, 15)
                                        .padding(.horizontal, 20)
                                        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                                        .colorScheme(.light)
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 20)
                                                .stroke(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255).opacity(0.4), lineWidth: 1)
                                        )
                                        .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
                                    }
                                }
                                .padding(20)
                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
                                .colorScheme(.light)
                            }
                            .padding(.horizontal, 20)
                            .padding(.vertical, 20)
                        }
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
        .onAppear {
            loadUserData()
        }
        .overlay(
            Group {
                if showingCloudPasswordReset {
                    PasswordResetWrapper(isCloudAccount: true) {
                        showingCloudPasswordReset = false
                    }
                    .transition(.move(edge: .trailing))
                    .zIndex(1)
                }
                if showingLocalPasswordReset {
                    PasswordResetWrapper(isCloudAccount: false) {
                        showingLocalPasswordReset = false
                    }
                    .transition(.move(edge: .trailing))
                    .zIndex(1)
                }
            }
        )
        .fullScreenCover(isPresented: $navigateToLogin) {
            Login()
        }
        .fullScreenCover(isPresented: $navigateToServerLogin) {
            ServerLogin()
        }
        .animation(.easeInOut(duration: 0.3), value: showingCloudPasswordReset)
        .animation(.easeInOut(duration: 0.3), value: showingLocalPasswordReset)
                        .toolbar {
                            ToolbarItem(placement: .navigationBarTrailing) {
                                Button("Done") {
                                    showingWebView = false
                                }
                            }
                        }
                }
            }
        }
    }
    
    private func loadUserData() {
        email = UserDefaults.standard.string(forKey: "user_email") ?? "Loading..."
        username = UserDefaults.standard.string(forKey: "user_username") ?? "Loading..."
        localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Loading..."
        
        fetchCloudSettings()
        fetchShareifySettings()
    }
    
    private func fetchCloudSettings() {
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty else {
            email = "Not available"
            username = "Not available"
            return
        }
        
        isLoadingCloudData = true
        
        guard let url = URL(string: "https://bridge.bbarni.hackclub.app/user/profile") else {
            email = "Error loading"
            username = "Error loading"
            isLoadingCloudData = false
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isLoadingCloudData = false
                
                if error != nil {
                    self.email = "Error loading"
                    self.username = "Error loading"
                    return
                }
                
                guard let data = data else {
                    self.email = "No data"
                    self.username = "No data"
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    self.email = "Error loading"
                    self.username = "Error loading"
                    return
                }
                
                if httpResponse.statusCode == 401 {
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let errorMessage = json["error"] as? String,
                       errorMessage == "Invalid or expired JWT token" {
                        self.refreshJWTTokenAndRetry {
                            self.fetchCloudSettings()
                        }
                        return
                    }
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        if let userEmail = json["email"] as? String {
                            self.email = userEmail
                            UserDefaults.standard.set(userEmail, forKey: "user_email")
                        }
                        if let userName = json["username"] as? String {
                            self.username = userName
                            UserDefaults.standard.set(userName, forKey: "user_username")
                        }
                        UserDefaults.standard.synchronize()
                    }
                } catch {
                    self.email = "Parse error"
                    self.username = "Parse error"
                }
            }
        }.resume()
    }
    
    private func fetchShareifySettings() {
        guard let jwtToken = UserDefaults.standard.string(forKey: "jwt_token"), !jwtToken.isEmpty,
              let shareifyJWT = UserDefaults.standard.string(forKey: "shareify_jwt"), !shareifyJWT.isEmpty else {
            localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Not available"
            return
        }
        
        isLoadingShareifyData = true
        
        guard let url = URL(string: "https://command.bbarni.hackclub.app/") else {
            localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Error loading"
            isLoadingShareifyData = false
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(jwtToken)", forHTTPHeaderField: "Authorization")
        request.setValue(shareifyJWT, forHTTPHeaderField: "X-Shareify-JWT")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let requestBody: [String: Any] = [
            "command": "/user/get_self"
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: requestBody)
        } catch {
            localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Request error"
            isLoadingShareifyData = false
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isLoadingShareifyData = false
                
                if error != nil {
                    self.localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Error loading"
                    return
                }
                
                guard let data = data else {
                    self.localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "No data"
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    self.localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Error loading"
                    return
                }
                
                if httpResponse.statusCode == 401 {
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let errorMessage = json["error"] as? String,
                       errorMessage == "Invalid or expired JWT token" {
                        self.refreshJWTTokenAndRetry {
                            self.fetchShareifySettings()
                        }
                        return
                    }
                }
                
                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] {
                        if let userName = json["username"] as? String {
                            self.localUsername = userName
                            UserDefaults.standard.set(userName, forKey: "server_username")
                            UserDefaults.standard.synchronize()
                        } else {
                            self.localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Not available"
                        }
                    }
                } catch {
                    self.localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Not available"
                }
            }
        }.resume()
    }
    
    private func logoutCloud() {
        UserDefaults.standard.removeObject(forKey: "jwt_token")
        UserDefaults.standard.removeObject(forKey: "user_email")
        UserDefaults.standard.removeObject(forKey: "user_username")
        UserDefaults.standard.removeObject(forKey: "user_password")
        UserDefaults.standard.removeObject(forKey: "server_username")
        UserDefaults.standard.removeObject(forKey: "server_password")
        UserDefaults.standard.removeObject(forKey: "shareify_jwt")
        UserDefaults.standard.synchronize()
        
        navigateToLogin = true
    }
    
    private func logoutLocal() {
        UserDefaults.standard.removeObject(forKey: "server_username")
        UserDefaults.standard.removeObject(forKey: "server_password")
        UserDefaults.standard.removeObject(forKey: "shareify_jwt")
        UserDefaults.standard.synchronize()
        
        navigateToServerLogin = true
    }
    
    private func refreshJWTTokenAndRetry(completion: @escaping () -> Void) {
        guard let email = UserDefaults.standard.string(forKey: "user_email"),
              let password = UserDefaults.standard.string(forKey: "user_password"),
              !email.isEmpty, !password.isEmpty else {
            return
        }
        
        guard let url = URL(string: "https://bridge.bbarni.hackclub.app/login") else {
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
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                guard let data = data,
                      let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode == 200,
                      let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let newJwtToken = json["jwt_token"] as? String else {
                    return
                }
                
                UserDefaults.standard.set(newJwtToken, forKey: "jwt_token")
                UserDefaults.standard.synchronize()
                completion()
            }
        }.resume()
    }
}


struct PasswordResetWrapper: View {
    let isCloudAccount: Bool
    let onDismiss: () -> Void
    
    var body: some View {
        ZStack {
            PasswordReset(isCloudAccount: isCloudAccount)
        }
        .gesture(
            DragGesture()
                .onEnded { value in
                    if value.translation.width > 100 {
                        onDismiss()
                    }
                }
        )
    }
}

#Preview {
    Settings()
}
