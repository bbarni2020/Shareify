//
//  OnboardingView.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 28..
//

import SwiftUI

struct OnboardingView: View {
    @State private var currentStep = 0
    @State private var animationOffset: CGFloat = 50
    @State private var animationOpacity: Double = 0
    @State private var logoScale: CGFloat = 0.8
    @Binding var isOnboardingComplete: Bool
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    let steps = [
        OnboardingStep(
            icon: "cloud.fill",
            title: "Welcome to Shareify",
            description: "Your personal cloud storage solution that keeps your files safe and accessible anywhere"
        ),
        OnboardingStep(
            icon: "lock.shield.fill",
            title: "Secure & Private",
            description: "Advanced encryption ensures your data remains private and secure with enterprise-grade protection"
        ),
        OnboardingStep(
            icon: "macbook.and.iphone",
            title: "Access Anywhere",
            description: "Sync your files across all devices and access them from anywhere in the world"
        ),
        OnboardingStep(
            icon: "person.2.fill",
            title: "Share with Ease",
            description: "Collaborate with friends and colleagues by sharing files and folders seamlessly"
        )
    ]
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                Spacer()
                
                Rectangle()
                    .foregroundColor(.clear)
                    .frame(width: min(geometry.size.width * 0.9, 380), height: min(geometry.size.height * 0.7, 500))
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 30))
                    .shadow(color: .white.opacity(0.25), radius: 10, x: 0, y: 8)
                    .overlay(
                        VStack(spacing: 0) {
                            HStack {
                                Spacer()
                                Button(action: {
                                    withAnimation(.easeInOut(duration: 0.5)) {
                                        isOnboardingComplete = true
                                    }
                                }) {
                                    Text("Skip")
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                }
                                .padding(.trailing, 25)
                                .padding(.top, 20)
                            }
                            
                            VStack(spacing: 40) {
                                ZStack {
                                    Circle()
                                        .fill(
                                            LinearGradient(
                                                gradient: Gradient(colors: [
                                                    Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255).opacity(0.1),
                                                    Color(red: 0x29/255, green: 0x6D/255, blue: 0xE0/255).opacity(0.1)
                                                ]),
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                        .frame(width: 120, height: 120)
                                    
                                    Image(systemName: steps[currentStep].icon)
                                        .font(.system(size: 40, weight: .medium))
                                        .foregroundColor(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255))
                                        .scaleEffect(logoScale)
                                        .animation(.spring(response: 0.6, dampingFraction: 0.8), value: logoScale)
                                        .frame(width: 120, height: 120)
                                }
                                
                                VStack(spacing: 20) {
                                    Text(steps[currentStep].title)
                                        .font(.system(size: 24, weight: .bold))
                                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        .multilineTextAlignment(.center)
                                        .offset(y: animationOffset)
                                        .opacity(animationOpacity)
                                        .animation(.easeOut(duration: 0.6).delay(0.2), value: animationOffset)
                                        .animation(.easeOut(duration: 0.6).delay(0.2), value: animationOpacity)
                                    
                                    Text(steps[currentStep].description)
                                        .font(.system(size: 16, weight: .medium))
                                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                        .multilineTextAlignment(.center)
                                        .lineLimit(nil)
                                        .offset(y: animationOffset)
                                        .opacity(animationOpacity)
                                        .animation(.easeOut(duration: 0.6).delay(0.4), value: animationOffset)
                                        .animation(.easeOut(duration: 0.6).delay(0.4), value: animationOpacity)
                                }
                                .padding(.horizontal, 30)
                                
                                VStack(spacing: 25) {
                                    HStack(spacing: 8) {
                                        ForEach(0..<steps.count, id: \.self) { index in
                                            RoundedRectangle(cornerRadius: 4)
                                                .fill(index == currentStep ? 
                                                      Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255) : 
                                                      Color.gray.opacity(0.3))
                                                .frame(width: index == currentStep ? 24 : 8, height: 8)
                                                .animation(.easeInOut(duration: 0.3), value: currentStep)
                                        }
                                    }
                                    
                                    HStack(spacing: 15) {
                                        if currentStep > 0 {
                                            Button(action: {
                                                goToPreviousStep()
                                            }) {
                                                Text("Back")
                                                    .font(.system(size: 16, weight: .medium))
                                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                                    .frame(width: 80, height: 45)
                                                    .background(
                                                        RoundedRectangle(cornerRadius: 12)
                                                            .fill(Color.white.opacity(0.8))
                                                            .overlay(
                                                                RoundedRectangle(cornerRadius: 12)
                                                                    .stroke(Color(red: 0xE5/255, green: 0xE7/255, blue: 0xEB/255), lineWidth: 1.5)
                                                            )
                                                            .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
                                                    )
                                            }
                                        }
                                        
                                        Spacer()
                                        
                                        Button(action: {
                                            if currentStep < steps.count - 1 {
                                                goToNextStep()
                                            } else {
                                                withAnimation(.easeInOut(duration: 0.5)) {
                                                    isOnboardingComplete = true
                                                }
                                            }
                                        }) {
                                            Text(currentStep < steps.count - 1 ? "Next" : "Get Started")
                                                .font(.system(size: 16, weight: .semibold))
                                                .foregroundColor(.white)
                                                .frame(width: currentStep < steps.count - 1 ? 80 : 120, height: 45)
                                                .background(
                                                    RoundedRectangle(cornerRadius: 12)
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
                                                .animation(.easeInOut(duration: 0.3), value: currentStep)
                                        }
                                    }
                                    .padding(.horizontal, 30)
                                }
                            }
                            .padding(.horizontal, 20)
                            .padding(.vertical, 30)
                        }
                    )
                
                Spacer()
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
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
                startAnimation()
            }
        }
    }
    
    private func startAnimation() {
        withAnimation(.easeOut(duration: 0.8)) {
            animationOffset = 0
            animationOpacity = 1
            logoScale = 1.0
        }
    }
    
    private func goToNextStep() {
        withAnimation(.easeInOut(duration: 0.3)) {
            animationOffset = 50
            animationOpacity = 0
            logoScale = 0.8
        }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            currentStep += 1
            withAnimation(.easeOut(duration: 0.6)) {
                animationOffset = 0
                animationOpacity = 1
                logoScale = 1.0
            }
        }
    }
    
    private func goToPreviousStep() {
        withAnimation(.easeInOut(duration: 0.3)) {
            animationOffset = -50
            animationOpacity = 0
            logoScale = 0.8
        }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            currentStep -= 1
            withAnimation(.easeOut(duration: 0.6)) {
                animationOffset = 0
                animationOpacity = 1
                logoScale = 1.0
            }
        }
    }
}

struct OnboardingStep {
    let icon: String
    let title: String
    let description: String
}

#Preview {
    OnboardingView(isOnboardingComplete: .constant(false))
}
