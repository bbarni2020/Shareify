//
//  Home.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 06. 26..
//

import SwiftUI
import Foundation

struct Home: View {
    @State private var isFlickering = false
    @State private var cpuValue: Double = 0
    @State private var memoryValue: Double = 0
    @State private var diskValue: Double = 0
    @State private var isLoaded = false
    @State private var topBarOpacity: Double = 0
    @State private var topBarOffset: CGFloat = -20
    @State private var mainCardOpacity: Double = 0
    @State private var mainCardOffset: CGFloat = 50
    @State private var navigateToLogin = false
    @State private var logs: [ServerLogEntry] = []
    @State private var hasServerError = false
    @State private var showStatusPopup = false
    @State private var lastSuccessfulCall: Date?
    
    var body: some View {
        GeometryReader { geometry in
            VStack(spacing: 0) {  
                HStack(alignment: .center, spacing: 10) {
                    Button(action: {
                        showStatusPopup = true
                    }) {
                        Rectangle()
                            .foregroundColor(.clear)
                            .frame(width: 238 * (50 / 62), height: 50)
                            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                            .overlay(
                                HStack(spacing: 10) {
                                    Circle()
                                        .fill(hasServerError ? Color.red : Color(red: 0x6F/255, green: 0xE6/255, blue: 0x8A/255))
                                        .frame(width: 13, height: 13)
                                        .opacity(hasServerError ? 1.0 : (isFlickering ? 0.0 : 1.0))
                                        .animation(hasServerError ? .none : .easeInOut(duration: 1.8).repeatForever(autoreverses: true), value: isFlickering)
                                        .onAppear {
                                            if !hasServerError {
                                                isFlickering = true
                                            }
                                        }
                                    Text("Shareify 2.")
                                        .foregroundColor(hasServerError ? Color.red : Color(red: 0x6F/255, green: 0xE6/255, blue: 0x8A/255))
                                        .font(.system(size: 16, weight: .medium))
                                }
                                .frame(maxWidth: .infinity)
                            )
                    }
                    Spacer()
                    Button(action: {
                        logout()
                    }) {
                        Rectangle()
                          .foregroundColor(.clear)
                          .frame(width: 50, height: 50)
                          .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 25))
                          .overlay(
                            Image(systemName: "power")
                                .font(.system(size: 18, weight: .medium))
                                .foregroundColor(Color.red)
                          )
                    }
                }
                .opacity(topBarOpacity)
                .offset(y: topBarOffset)
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
                  .opacity(mainCardOpacity)
                  .offset(y: mainCardOffset)
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
                                loadResources()
                                loadLogs()
                            }
                            
                            Spacer().frame(height: min(containerGeometry.size.height * 0.05, 30))
                            
                            HStack {
                                Text("Logs")
                                    .font(.system(size: min(containerGeometry.size.width * 0.06, 24), weight: .medium))
                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                Spacer()
                            }
                            .padding(.bottom, min(containerGeometry.size.height * 0.02, 10))
                            
                            LogsTableView(logs: logs)
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
            .onAppear {
                startHomeAnimation()
            }
        )
        .fullScreenCover(isPresented: $navigateToLogin) {
            Login()
        }
        .onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("RedirectToLogin"))) { _ in
            navigateToLogin = true
        }
        .onReceive(NotificationCenter.default.publisher(for: NSNotification.Name("ShowServerError"))) { _ in
            withAnimation(.easeInOut(duration: 0.3)) {
                hasServerError = true
                isFlickering = false
            }
        }
        .overlay(
            Group {
                if showStatusPopup {
                    Color.black.opacity(0.3)
                        .ignoresSafeArea()
                        .onTapGesture {
                            showStatusPopup = false
                        }
                    
                    VStack(spacing: 20) {
                        HStack {
                            Text("Server Status")
                                .font(.system(size: 20, weight: .semibold))
                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                            Spacer()
                            Button(action: {
                                showStatusPopup = false
                            }) {
                                Image(systemName: "xmark.circle.fill")
                                    .font(.system(size: 20))
                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.5))
                            }
                        }
                        
                        VStack(spacing: 15) {
                            HStack(spacing: 10) {
                                Circle()
                                    .fill(hasServerError ? Color.red : Color(red: 0x6F/255, green: 0xE6/255, blue: 0x8A/255))
                                    .frame(width: 12, height: 12)
                                
                                Text(hasServerError ? "Your Shareify server isn't running or isn't accessible from the internet" : "Your Shareify server is accessible and running fine")
                                    .font(.system(size: 16, weight: .medium))
                                    .foregroundColor(hasServerError ? Color.red : Color(red: 0x6F/255, green: 0xE6/255, blue: 0x8A/255))
                                    .multilineTextAlignment(.leading)
                                Spacer()
                            }
                            
                            if let lastCall = lastSuccessfulCall {
                                HStack {
                                    Text("Last successful call:")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                    Spacer()
                                    Text(formatDate(lastCall))
                                        .font(.system(size: 14, weight: .medium, design: .monospaced))
                                        .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                }
                            } else {
                                HStack {
                                    Text("No successful calls yet")
                                        .font(.system(size: 14, weight: .medium))
                                        .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                    Spacer()
                                }
                            }
                        }
                    }
                    .padding(25)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                    .padding(.horizontal, 40)
                    .transition(.scale.combined(with: .opacity))
                }
            }
        )
        .animation(.spring(response: 0.6, dampingFraction: 0.8), value: showStatusPopup)
    }
    
    private func resetServerErrorState() {
        withAnimation(.easeInOut(duration: 0.3)) {
            hasServerError = false
            isFlickering = true
        }
        lastSuccessfulCall = Date()
    }
    
    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MM/dd HH:mm:ss"
        return formatter.string(from: date)
    }
    
    private func logout() {
        UserDefaults.standard.removeObject(forKey: "jwt_token")
        UserDefaults.standard.removeObject(forKey: "server_username")
        UserDefaults.standard.removeObject(forKey: "server_password")
        UserDefaults.standard.synchronize()
        
        withAnimation(.easeInOut(duration: 0.5)) {
            navigateToLogin = true
        }
    }
    
    private func startHomeAnimation() {
        withAnimation(.easeOut(duration: 0.6)) {
            topBarOpacity = 1.0
            topBarOffset = 0
        }
        
        withAnimation(.easeOut(duration: 0.8).delay(0.2)) {
            mainCardOpacity = 1.0
            mainCardOffset = 0
        }
    }
    
    private func startLoadingAnimation() {
        withAnimation(.easeInOut(duration: 2.0)) {
            isLoaded = true
        }
    }
    
    private func startValueUpdates() {
        Timer.scheduledTimer(withTimeInterval: 30.0, repeats: true) { _ in
            loadResources()
        }
    }
    
    private func loadResources() {
        print("DEBUG: Home.loadResources() called")
        ServerManager.shared.executeServerCommand(command: "/resources", method: "GET") { result in
            switch result {
            case .success(let response):
                print("DEBUG: Resources loaded successfully")
                resetServerErrorState()
                DispatchQueue.main.async {
                    if let responseDict = response as? [String: Any] {
                        if let cpu = responseDict["cpu"] as? Int {
                            withAnimation(.easeInOut(duration: 1.5)) {
                                self.cpuValue = Double(cpu)
                            }
                        }
                        if let memory = responseDict["memory"] as? Int {
                            withAnimation(.easeInOut(duration: 1.5)) {
                                self.memoryValue = Double(memory)
                            }
                        }
                        if let disk = responseDict["disk"] as? Int {
                            withAnimation(.easeInOut(duration: 1.5)) {
                                self.diskValue = Double(disk)
                            }
                        }
                    }
                }
            case .failure(let error):
                print("DEBUG: Resources loading failed with error: \(error)")
                withAnimation(.easeInOut(duration: 0.3)) {
                    hasServerError = true
                    isFlickering = false
                }
                break
            }
        }
    }
    
    private func loadLogs() {
        print("DEBUG: Home.loadLogs() called")
        let requestBody = ["wait_time": 5]
        ServerManager.shared.executeServerCommand(command: "/get_logs", method: "GET", body: requestBody) { result in
            switch result {
            case .success(let response):
                print("DEBUG: Logs loaded successfully")
                resetServerErrorState()
                var logsArray: [[String: Any]] = []
                
                if let directArray = response as? [[String: Any]] {
                    logsArray = directArray
                } else if let responseDict = response as? [String: Any],
                          let nestedArray = responseDict["logs"] as? [[String: Any]] {
                    logsArray = nestedArray
                }
                
                let serverLogs = logsArray.compactMap { logDict -> ServerLogEntry? in
                    guard let action = logDict["action"] as? String,
                          let timestamp = logDict["timestamp"] as? String,
                          let id = logDict["id"] as? Int,
                          let ip = logDict["ip"] as? String else {
                        return nil
                    }
                    
                    let dateFormatter = DateFormatter()
                    dateFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
                    
                    let displayDateTime: String
                    if let date = dateFormatter.date(from: timestamp) {
                        let displayFormatter = DateFormatter()
                        displayFormatter.dateFormat = "MM/dd HH:mm:ss"
                        displayDateTime = displayFormatter.string(from: date)
                    } else {
                        displayDateTime = timestamp
                    }
                    
                    let level = determineLogLevel(action: action)
                    
                    return ServerLogEntry(time: displayDateTime, action: action, ipAddress: ip, level: level, id: id)
                }
                
                DispatchQueue.main.async {
                    withAnimation(.easeInOut(duration: 0.5)) {
                        self.logs = serverLogs
                    }
                }
                
            case .failure(let error):
                print("DEBUG: Logs loading failed with error: \(error)")
                withAnimation(.easeInOut(duration: 0.3)) {
                    hasServerError = true
                    isFlickering = false
                }
                break
            }
        }
    }
    
    private func determineLogLevel(action: String) -> LogLevel {
        let lowercasedAction = action.lowercased()
        if lowercasedAction.contains("error") || lowercasedAction.contains("unauthorized") || lowercasedAction.contains("failed") {
            return .error
        } else if lowercasedAction.contains("warning") || lowercasedAction.contains("attempt") {
            return .warning
        } else if lowercasedAction.contains("logged in") || lowercasedAction.contains("success") {
            return .success
        } else {
            return .info
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
        .onChange(of: value) { _, newValue in
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

struct ServerLogEntry {
    let time: String
    let action: String
    let ipAddress: String
    let level: LogLevel
    let id: Int
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
    let logs: [ServerLogEntry]
    
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Text("Date & Time")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.8))
                    .frame(width: 100, alignment: .leading)
                
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
            
            if logs.isEmpty {
                VStack {
                    Spacer()
                    Text("Loading logs...")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.6))
                    Spacer()
                }
                .frame(height: 100)
            } else {
                ScrollView {
                    LazyVStack(spacing: 1) {
                        ForEach(Array(logs.enumerated()), id: \.element.id) { index, log in
                            HStack(spacing: 12) {
                                Text(log.time)
                                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                                    .frame(width: 100, alignment: .leading)
                                
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
