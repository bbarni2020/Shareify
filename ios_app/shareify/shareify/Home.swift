//
//  Home.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 26..
//

import SwiftUI

struct Home: View {
    @State private var isFlickering = false
    @State private var cpuValue: Double = 0
    @State private var memoryValue: Double = 0
    @State private var diskValue: Double = 0
    @State private var isLoaded = false
    
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
                  .overlay(
                    GeometryReader { containerGeometry in
                        VStack(alignment: .leading) {
                            Spacer()
                            
                            HStack {
                                Text("Resources")
                                    .font(.system(size: min(containerGeometry.size.width * 0.06, 24), weight: .medium))
                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                Spacer()
                            }
                            .padding(.bottom, min(containerGeometry.size.height * 0.04, 20))
                            
                            HStack(spacing: min(containerGeometry.size.width * 0.08, 48)) {
                                let meterSize = min(containerGeometry.size.width * 0.25, containerGeometry.size.height * 0.3, 120)
                                SpeedometerView(value: cpuValue, color: Color(red: 0x65/255, green: 0xdc/255, blue: 0x50/255), label: "CPU", size: meterSize)
                                SpeedometerView(value: memoryValue, color: Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255), label: "Memory", size: meterSize)
                                SpeedometerView(value: diskValue, color: Color(red: 0xf5/255, green: 0x9e/255, blue: 0x42/255), label: "Disk", size: meterSize)
                            }
                            .onAppear {
                                startLoadingAnimation()
                                startValueUpdates()
                            }
                            
                            Spacer().frame(height: min(containerGeometry.size.height * 0.05, 30))
                            
                            HStack {
                                Text("Logs")
                                    .font(.system(size: min(containerGeometry.size.width * 0.06, 24), weight: .medium))
                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                Spacer()
                            }
                            .padding(.bottom, min(containerGeometry.size.height * 0.02, 10))
                            
                            LogsTableView()
                                .frame(maxHeight: min(containerGeometry.size.height * 0.6, 250))
                            
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
    
    private func startLoadingAnimation() {
        withAnimation(.easeInOut(duration: 2.0)) {
            cpuValue = 45
            memoryValue = 67
            diskValue = 23
            isLoaded = true
        }
    }
    
    private func startValueUpdates() {
        Timer.scheduledTimer(withTimeInterval: 3.0, repeats: true) { _ in
            withAnimation(.easeInOut(duration: 1.5)) {
                cpuValue = Double.random(in: 15...85)
                memoryValue = Double.random(in: 30...90)
                diskValue = Double.random(in: 10...70)
            }
        }
    }
}

struct SpeedometerView: View {
    let value: Double
    let color: Color
    let label: String
    let size: CGFloat
    @State private var animatedValue: Double = 0
    
    var body: some View {
        VStack(spacing: size * 0.08) {
            ZStack {
                Circle()
                    .stroke(Color(red: 0xbf/255, green: 0xc6/255, blue: 0xd1/255), lineWidth: size * 0.108)
                    .frame(width: size, height: size)
                
                Circle()
                    .trim(from: 0, to: animatedValue / 100)
                    .stroke(color, style: StrokeStyle(lineWidth: size * 0.108, lineCap: .round))
                    .frame(width: size, height: size)
                    .rotationEffect(.degrees(-90))
                    .animation(.spring(response: 1.0, dampingFraction: 0.8, blendDuration: 0.5), value: animatedValue)
                
                Text("\(Int(animatedValue))%")
                    .font(.system(size: size * 0.233, weight: .bold))
                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                    .contentTransition(.numericText())
                    .animation(.easeInOut(duration: 0.8), value: animatedValue)
            }
            
            Text(label)
                .font(.system(size: size * 0.133, weight: .medium))
                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                .tracking(1)
        }
        .onChange(of: value) { newValue in
            withAnimation(.spring(response: 1.0, dampingFraction: 0.8, blendDuration: 0.5)) {
                animatedValue = newValue
            }
        }
        .onAppear {
            withAnimation(.spring(response: 1.5, dampingFraction: 0.6, blendDuration: 0.8).delay(Double.random(in: 0...0.5))) {
                animatedValue = value
            }
        }
    }
}

struct LogEntry {
    let time: String
    let action: String
    let ipAddress: String
    let level: LogLevel
}

enum LogLevel {
    case info, warning, error, success
    
    var color: Color {
        switch self {
        case .info:
            return Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255)
        case .warning:
            return Color(red: 0xf5/255, green: 0x9e/255, blue: 0x42/255)
        case .error:
            return Color.red
        case .success:
            return Color(red: 0x65/255, green: 0xdc/255, blue: 0x50/255)
        }
    }
    
    var icon: String {
        switch self {
        case .info:
            return "info.circle.fill"
        case .warning:
            return "exclamationmark.triangle.fill"
        case .error:
            return "xmark.circle.fill"
        case .success:
            return "checkmark.circle.fill"
        }
    }
}

struct LogsTableView: View {
    private let sampleLogs = [
        LogEntry(time: "14:32:18", action: "Server started", ipAddress: "127.0.0.1", level: .success),
        LogEntry(time: "14:32:25", action: "Client connected", ipAddress: "192.168.1.100", level: .info),
        LogEntry(time: "14:33:02", action: "File uploaded", ipAddress: "192.168.1.105", level: .success),
        LogEntry(time: "14:33:15", action: "Authentication failed", ipAddress: "192.168.1.200", level: .warning),
        LogEntry(time: "14:33:28", action: "Connection timeout", ipAddress: "10.0.0.50", level: .error),
        LogEntry(time: "14:34:01", action: "File downloaded", ipAddress: "192.168.1.100", level: .info)
    ]
    
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Text("Time")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.8))
                    .frame(width: 60, alignment: .leading)
                
                Text("Action")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.8))
                    .frame(maxWidth: .infinity, alignment: .leading)
                
                Text("IP Address")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.8))
                    .frame(width: 100, alignment: .trailing)
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.08))
            
            ScrollView {
                LazyVStack(spacing: 1) {
                    ForEach(Array(sampleLogs.enumerated()), id: \.offset) { index, log in
                        HStack(spacing: 12) {
                            Text(log.time)
                                .font(.system(size: 12, weight: .medium, design: .monospaced))
                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                .frame(width: 60, alignment: .leading)
                            
                            Text(log.action)
                                .font(.system(size: 13, weight: .regular))
                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .lineLimit(1)
                            
                            Text(log.ipAddress)
                                .font(.system(size: 12, weight: .medium, design: .monospaced))
                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.6))
                                .frame(width: 100, alignment: .trailing)
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(
                            index % 2 == 0 
                            ? Color.clear 
                            : Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.02)
                        )
                    }
                }
            }
        }
        .background(
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.05))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.1), lineWidth: 1)
                )
        )
    }
}

#Preview {
    Home()
}
