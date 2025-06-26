//
//  Home.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 26..
//

import SwiftUI

struct Home: View {
    @State private var isFlickering = false
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {
                HStack(alignment: .center, spacing: 10) {
                    Rectangle()
                        .foregroundColor(.clear)
                        .frame(width: 238 * (50 / 62), height: 50)
                        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                        .overlay(
                            HStack(spacing: 10) {
                                Circle()
                                    .fill(Color(red: 0x6F/255, green: 0xE6/255, blue: 0x8A/255))
                                    .frame(width: 13, height: 13)
                                    .opacity(isFlickering ? 0.0 : 1.0)
                                    .animation(.easeInOut(duration: 1.8).repeatForever(autoreverses: true), value: isFlickering)
                                    .onAppear {
                                        isFlickering = true
                                    }
                                Text("Shareify 2.")
                                    .foregroundColor(Color(red: 0x6F/255, green: 0xE6/255, blue: 0x8A/255))
                                    .font(.system(size: 16, weight: .medium))
                            }
                            .frame(maxWidth: .infinity)
                        )
                    Spacer()
                    Rectangle()
                      .foregroundColor(.clear)
                      .frame(width: 50, height: 50)
                      .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
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
            }
        }
        .background(
            GeometryReader { geometry in
                AsyncImage(url: URL(string: "https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/ios_app/background/back15.png")) { image in
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
}

#Preview {
    Home()
}
