//
//  AppLoad.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 28..
//

import SwiftUI

struct AppLoad: View {
    @State private var logoScale: CGFloat = 0.8
    @State private var logoOpacity: Double = 0
    @State private var titleOffset: CGFloat = 30
    @State private var titleOpacity: Double = 0
    @State private var progressOpacity: Double = 0
    @State private var progressWidth: CGFloat = 0
    @State private var cardOpacity: Double = 0
    @State private var isAnimating = false
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 40) {
                Spacer()
                
                Rectangle()
                    .foregroundColor(.clear)
                    .frame(width: min(geometry.size.width * 0.85, 350), height: 400)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                    .colorScheme(.light)
                    .shadow(color: .white.opacity(0.25), radius: 8, x: 0, y: 4)
                    .opacity(cardOpacity)
                    .overlay(
                        VStack(spacing: 35) {
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
                                    .frame(width: 140, height: 140)
                                    .scaleEffect(logoScale)
                                    .opacity(logoOpacity)
                                
                                Image(systemName: "icloud.fill")
                                    .font(.system(size: 50, weight: .medium))
                                    .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                                    .scaleEffect(logoScale)
                                    .opacity(logoOpacity)
                            }
                            
                            VStack(spacing: 12) {
                                Text("Shareify")
                                    .font(.system(size: 32, weight: .bold))
                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                    .offset(y: titleOffset)
                                    .opacity(titleOpacity)
                                
                                Text("Your files, everywhere")
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                    .offset(y: titleOffset)
                                    .opacity(titleOpacity)
                            }
                            
                            VStack(spacing: 15) {
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255).opacity(0.2))
                                    .frame(width: 200, height: 6)
                                    .overlay(
                                        RoundedRectangle(cornerRadius: 8)
                                            .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                                            .frame(width: progressWidth)
                                            .animation(.easeInOut(duration: 2.0), value: progressWidth),
                                        alignment: .leading
                                    )
                                    .opacity(progressOpacity)
                                
                                Text("Loading...")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                    .opacity(progressOpacity)
                            }
                        }
                        .padding(.horizontal, 30)
                        .padding(.vertical, 40)
                    )
                
                Spacer()
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(
                GeometryReader { geometry in
                    Image("back1")
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: geometry.size.height * (1533/862), height: geometry.size.height)
                        .offset(x: -geometry.size.height * (1533/862) * 0.274)
                        .clipped()
                }
                .ignoresSafeArea(.all)
            )
            .onAppear {
                startLoadingAnimation()
            }
        }
    }
    
    private func startLoadingAnimation() {
        withAnimation(.spring(response: 0.8, dampingFraction: 0.6)) {
            logoScale = 1.0
            logoOpacity = 1.0
            cardOpacity = 1.0
        }
        
        withAnimation(.easeOut(duration: 0.8).delay(0.3)) {
            titleOffset = 0
            titleOpacity = 1.0
        }
        
        withAnimation(.easeOut(duration: 0.6).delay(0.6)) {
            progressOpacity = 1.0
        }
        
        withAnimation(.easeInOut(duration: 2.0).delay(0.8)) {
            progressWidth = 200
        }
        
        withAnimation(.easeOut(duration: 0.8).delay(3.0)) {
            cardOpacity = 0
            logoOpacity = 0
            titleOpacity = 0
            progressOpacity = 0
        }
    }
}

#Preview {
    AppLoad()
}
