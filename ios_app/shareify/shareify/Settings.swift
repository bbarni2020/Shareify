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
    @State private var newPassword: String = ""
    @State private var confirmPassword: String = ""
    @State private var localUsername: String = ""
    @State private var newLocalPassword: String = ""
    @State private var confirmLocalPassword: String = ""
    @State private var selectedBackground: Int = 1
    @State private var showingPasswordAlert = false
    @State private var showingLocalPasswordAlert = false
    @State private var alertMessage = ""
    @State private var navigateToLogin = false
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
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .frame(width: 80, alignment: .leading)
                                            Text(email)
                                                .font(.system(size: 16, weight: .regular))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                            Spacer()
                                        }
                                        
                                        HStack {
                                            Text("Username:")
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .frame(width: 80, alignment: .leading)
                                            Text(username)
                                                .font(.system(size: 16, weight: .regular))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                            Spacer()
                                        }
                                        
                                        VStack(spacing: 10) {
                                            SecureField("New Password", text: $newPassword)
                                                .padding(.horizontal, 15)
                                                .padding(.vertical, 12)
                                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 25)
                                                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                                )
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                            
                                            SecureField("Confirm Password", text: $confirmPassword)
                                                .padding(.horizontal, 15)
                                                .padding(.vertical, 12)
                                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 25)
                                                        .stroke(Color.white.opacity(0.3), lineWidth: 1)
                                                )
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                            
                                            Button(action: changeCloudPassword) {
                                                Text("Change Password")
                                                    .font(.system(size: 16, weight: .medium))
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
                                            .disabled(newPassword.isEmpty || confirmPassword.isEmpty)
                                        }
                                        
                                        Button(action: logoutCloud) {
                                            Text("Logout Cloud Account")
                                                .font(.system(size: 16, weight: .medium))
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
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .frame(width: 80, alignment: .leading)
                                            Text(localUsername)
                                                .font(.system(size: 16, weight: .regular))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                            Spacer()
                                        }
                                        
                                        VStack(spacing: 10) {
                                            SecureField("New Local Password", text: $newLocalPassword)
                                                .padding(.horizontal, 15)
                                                .padding(.vertical, 12)
                                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 20)
                                                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                                )
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
                                            
                                            SecureField("Confirm Local Password", text: $confirmLocalPassword)
                                                .padding(.horizontal, 15)
                                                .padding(.vertical, 12)
                                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                                                .overlay(
                                                    RoundedRectangle(cornerRadius: 20)
                                                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                                )
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                                .shadow(color: .black.opacity(0.1), radius: 2, x: 0, y: 1)
                                            
                                            Button(action: changeLocalPassword) {
                                                Text("Change Local Password")
                                                    .font(.system(size: 16, weight: .medium))
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
                                            .disabled(newLocalPassword.isEmpty || confirmLocalPassword.isEmpty)
                                            .opacity(newLocalPassword.isEmpty || confirmLocalPassword.isEmpty ? 0.6 : 1.0)
                                        }
                                        
                                        VStack(alignment: .leading, spacing: 10) {
                                            Text("Background:")
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                            
                                            ScrollView(.horizontal, showsIndicators: false) {
                                                HStack(spacing: 15) {
                                                    ForEach(backgroundOptions, id: \.self) { backgroundNumber in
                                                        AsyncImage(url: URL(string: "https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/ios_app/background/back\(backgroundNumber).png")) { image in
                                                            image
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
                                                        } placeholder: {
                                                            Rectangle()
                                                                .fill(Color.gray.opacity(0.3))
                                                                .frame(width: 80, height: 60)
                                                                .cornerRadius(15)
                                                        }
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
                                                .font(.system(size: 16, weight: .medium))
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
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 20)
                                                .stroke(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255).opacity(0.4), lineWidth: 1)
                                        )
                                        .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
                                    }
                                }
                                .padding(20)
                                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
                            }
                            .padding(.horizontal, 20)
                            .padding(.vertical, 20)
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
        .onAppear {
            loadUserData()
        }
        .alert("Password Change", isPresented: $showingPasswordAlert) {
            Button("OK") { }
        } message: {
            Text(alertMessage)
        }
        .alert("Local Password Change", isPresented: $showingLocalPasswordAlert) {
            Button("OK") { }
        } message: {
            Text(alertMessage)
        }
        .fullScreenCover(isPresented: $navigateToLogin) {
            Login()
        }
    }
    
    private func loadUserData() {
        email = UserDefaults.standard.string(forKey: "user_email") ?? "Not available"
        username = UserDefaults.standard.string(forKey: "user_username") ?? "Not available"
        localUsername = UserDefaults.standard.string(forKey: "server_username") ?? "Not available"
    }
    
    private func changeCloudPassword() {
        guard newPassword == confirmPassword else {
            alertMessage = "Passwords do not match"
            showingPasswordAlert = true
            return
        }
        
        guard newPassword.count >= 6 else {
            alertMessage = "Password must be at least 6 characters"
            showingPasswordAlert = true
            return
        }
        
        alertMessage = "Password change functionality will be implemented"
        showingPasswordAlert = true
        
        newPassword = ""
        confirmPassword = ""
    }
    
    private func changeLocalPassword() {
        guard newLocalPassword == confirmLocalPassword else {
            alertMessage = "Passwords do not match"
            showingLocalPasswordAlert = true
            return
        }
        
        guard newLocalPassword.count >= 6 else {
            alertMessage = "Password must be at least 6 characters"
            showingLocalPasswordAlert = true
            return
        }
        
        UserDefaults.standard.set(newLocalPassword, forKey: "server_password")
        UserDefaults.standard.synchronize()
        
        alertMessage = "Local password updated successfully"
        showingLocalPasswordAlert = true
        
        newLocalPassword = ""
        confirmLocalPassword = ""
    }
    
    private func logoutCloud() {
        UserDefaults.standard.removeObject(forKey: "jwt_token")
        UserDefaults.standard.removeObject(forKey: "user_email")
        UserDefaults.standard.removeObject(forKey: "user_username")
        UserDefaults.standard.synchronize()
        
        navigateToLogin = true
    }
    
    private func logoutLocal() {
        UserDefaults.standard.removeObject(forKey: "server_username")
        UserDefaults.standard.removeObject(forKey: "server_password")
        UserDefaults.standard.removeObject(forKey: "shareify_jwt")
        UserDefaults.standard.synchronize()
        
        navigateToLogin = true
    }
    
    private func openGitHubGuides() {
        if let url = URL(string: "https://github.com/bbarni2020/Shareify/tree/main/guides") {
            UIApplication.shared.open(url)
        }
    }
}

#Preview {
    Settings()
}
