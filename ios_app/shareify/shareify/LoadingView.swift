//
//  LoadingView.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 28..
//

import SwiftUI

struct LoadingView: View {
    @State private var rotationAngle: Double = 0
    @State private var pulseScale: CGFloat = 1.0
    @State private var cardOpacity: Double = 0
    @State private var cardScale: CGFloat = 0.9
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                Spacer()
                
                Rectangle()
                    .foregroundColor(.clear)
                    .frame(width: min(geometry.size.width * 0.8, 320), height: 200)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                    .colorScheme(.light)
                    .shadow(color: .white.opacity(0.25), radius: 8, x: 0, y: 4)
                    .scaleEffect(cardScale)
                    .opacity(cardOpacity)
                    .overlay(
                        VStack(spacing: 35) {
                            ZStack {
                                Circle()
                                    .stroke(Color.white.opacity(0.2), lineWidth: 3)
                                    .frame(width: 60, height: 60)
                                
                                Circle()
                                    .trim(from: 0, to: 0.7)
                                    .stroke(
                                        LinearGradient(
                                            gradient: Gradient(colors: [
                                                Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255),
                                                Color(red: 0x29/255, green: 0x6D/255, blue: 0xE0/255)
                                            ]),
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        ),
                                        style: StrokeStyle(lineWidth: 3, lineCap: .round)
                                    )
                                    .frame(width: 60, height: 60)
                                    .rotationEffect(.degrees(rotationAngle))
                                    .animation(.linear(duration: 1.5).repeatForever(autoreverses: false), value: rotationAngle)
                            }
                            .scaleEffect(pulseScale)
                            .animation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true), value: pulseScale)
                            
                            VStack(spacing: 8) {
                                Text("Loading")
                                    .font(.system(size: 20, weight: .semibold))
                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                
                                Text("Please wait while we prepare everything for you")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                                    .multilineTextAlignment(.center)
                                    .opacity(0.8)
                            }
                        }
                        .padding(.horizontal, 30)
                    )
                
                Spacer()
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            GeometryReader { geometry in
                AsyncImage(url: URL(string: "https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/ios_app/background/back1.png")) { image in
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
            cardOpacity = 1.0
            cardScale = 1.0
        }
        
        withAnimation(.linear(duration: 1.5).repeatForever(autoreverses: false).delay(0.3)) {
            rotationAngle = 360
        }
        
        withAnimation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true).delay(0.3)) {
            pulseScale = 1.15
        }
    }
}

#Preview {
    LoadingView()
}
