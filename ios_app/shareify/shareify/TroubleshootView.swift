import SwiftUI

struct TroubleshootView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var showingDiagnostics = false
    @State private var diagnosticsResult = ""
    @State private var isRunningDiagnostics = false
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    var body: some View {
        GeometryReader { geometry in
            Image(backgroundManager.backgroundImageName)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: geometry.size.width, height: geometry.size.height)
                .clipped()
                .ignoresSafeArea(.all)
                .overlay(
                    Rectangle()
                        .foregroundColor(.clear)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .background(.ultraThinMaterial)
                        .colorScheme(.light)
                        .ignoresSafeArea(.all)
                        .overlay(
                            VStack(spacing: 0) {
                                topNavigationBar
                                
                                ScrollView {
                                    VStack(spacing: 20) {
                                        connectionIssuesSection
                                        
                                        commonProblemsSection
                                        
                                        diagnosticsSection
                                        
                                        contactSupportSection
                                    }
                                    .padding(.horizontal, 20)
                                    .padding(.top, 20)
                                }
                            }
                        )
                )
        }
        .ignoresSafeArea(.all)
        .overlay(
            Group {
                if showingDiagnostics {
                    Color.black.opacity(0.3)
                        .ignoresSafeArea()
                        .onTapGesture {
                            showingDiagnostics = false
                        }
                    
                    VStack(spacing: 20) {
                        HStack {
                            Text("Diagnostics Results")
                                .font(.system(size: 20, weight: .semibold))
                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                            Spacer()
                            Button(action: {
                                showingDiagnostics = false
                            }) {
                                Image(systemName: "xmark.circle.fill")
                                    .font(.system(size: 20))
                                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.5))
                            }
                        }
                        
                        ScrollView {
                            Text(diagnosticsResult)
                                .font(.system(size: 12, weight: .regular, design: .monospaced))
                                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding()
                                .background(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.05))
                                .cornerRadius(8)
                        }
                        .frame(maxHeight: 300)
                    }
                    .padding(25)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                    .colorScheme(.light)
                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                    .padding(.horizontal, 40)
                    .transition(.scale.combined(with: .opacity))
                }
            }
        )
        .animation(.spring(response: 0.6, dampingFraction: 0.8), value: showingDiagnostics)
    }
    
    private var topNavigationBar: some View {
        HStack {
            Button(action: {
                dismiss()
            }) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            Spacer()
            
            Text("Troubleshoot")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            
            Spacer()
            
            Button(action: {
                runDiagnostics()
            }) {
                Image(systemName: "stethoscope")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 60)
        .padding(.bottom, 10)
    }
    
    private var connectionIssuesSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Connection Issues")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
            
            VStack(spacing: 12) {
                troubleshootItem(
                    icon: "wifi.exclamationmark",
                    title: "Server Not Responding",
                    description: "Check if your Shareify server is running and accessible from the internet"
                )
                
                troubleshootItem(
                    icon: "lock.shield",
                    title: "Authentication Failed",
                    description: "Verify your username and password are correct in Settings"
                )
                
                troubleshootItem(
                    icon: "network",
                    title: "Network Connection",
                    description: "Ensure your device has a stable internet connection"
                )
            }
        }
        .padding(20)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
        .colorScheme(.light)
    }
    
    private var commonProblemsSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Common Problems")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
            
            VStack(spacing: 12) {
                troubleshootItem(
                    icon: "folder.badge.questionmark",
                    title: "Files Not Loading",
                    description: "Check server permissions and file access rights"
                )
                
                troubleshootItem(
                    icon: "chart.bar.xaxis",
                    title: "Resource Meters Empty",
                    description: "Server monitoring may be disabled or unavailable"
                )
                
                troubleshootItem(
                    icon: "list.bullet.rectangle",
                    title: "Logs Not Displaying",
                    description: "Server logging may be disabled or database issues"
                )
            }
        }
        .padding(20)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
        .colorScheme(.light)
    }
    
    private var diagnosticsSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Diagnostics")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
            
            Button(action: {
                runDiagnostics()
            }) {
                HStack {
                    if isRunningDiagnostics {
                        ProgressView()
                            .scaleEffect(0.8)
                            .foregroundColor(.white)
                    } else {
                        Image(systemName: "stethoscope")
                            .font(.system(size: 16))
                    }
                    
                    Text(isRunningDiagnostics ? "Running Diagnostics..." : "Run Connection Test")
                        .font(.system(size: 16, weight: .semibold))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255))
                .cornerRadius(10)
            }
            .disabled(isRunningDiagnostics)
            
            Text("This will test your server connection and provide detailed information about any issues.")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
        }
        .padding(20)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
        .colorScheme(.light)
    }
    
    private var contactSupportSection: some View {
        VStack(alignment: .leading, spacing: 15) {
            Text("Still Need Help?")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
            
            VStack(spacing: 12) {
                HStack {
                    Image(systemName: "doc.text")
                        .font(.system(size: 16))
                        .foregroundColor(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255))
                        .frame(width: 24)
                    
                    Text("Check the documentation at github.com/bbarni2020/Shareify")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                    
                    Spacer()
                }
                
                HStack {
                    Image(systemName: "envelope")
                        .font(.system(size: 16))
                        .foregroundColor(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255))
                        .frame(width: 24)
                    
                    Text("Contact support through GitHub Issues")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                    
                    Spacer()
                }
            }
        }
        .padding(20)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 15))
        .colorScheme(.light)
    }
    
    private func troubleshootItem(icon: String, title: String, description: String) -> some View {
        HStack(spacing: 15) {
            Image(systemName: icon)
                .font(.system(size: 20))
                .foregroundColor(Color(red: 0x3b/255, green: 0x82/255, blue: 0xf6/255))
                .frame(width: 30)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255))
                
                Text(description)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.7))
                    .fixedSize(horizontal: false, vertical: true)
            }
            
            Spacer()
        }
        .padding(15)
        .background(Color(red: 0x3C/255, green: 0x43/255, blue: 0x47/255).opacity(0.05))
        .cornerRadius(10)
    }
    
    private func runDiagnostics() {
        isRunningDiagnostics = true
        var result = "=== SHAREIFY DIAGNOSTICS REPORT ===\n\n"
        result += "Timestamp: \(Date())\n\n"
        
        result += "1. CHECKING USER CREDENTIALS...\n"
        let jwtToken = UserDefaults.standard.string(forKey: "jwt_token")
        let shareifyJWT = UserDefaults.standard.string(forKey: "shareify_jwt")
        let username = UserDefaults.standard.string(forKey: "server_username")
        
        result += "   JWT Token: \(jwtToken != nil ? "✓ Present" : "✗ Missing")\n"
        result += "   Shareify JWT: \(shareifyJWT != nil ? "✓ Present" : "✗ Missing")\n"
        result += "   Username: \(username != nil ? "✓ Present" : "✗ Missing")\n\n"
        
        result += "2. TESTING SERVER CONNECTION...\n"
        
        ServerManager.shared.executeServerCommand(command: "/is_up", method: "GET", waitTime: 3) { connectionResult in
            DispatchQueue.main.async {
                switch connectionResult {
                case .success(let response):
                    result += "   Server Status: ✓ Online\n"
                    result += "   Response: \(response)\n\n"
                case .failure(let error):
                    result += "   Server Status: ✗ Offline\n"
                    result += "   Error: \(error.localizedDescription)\n\n"
                }
                
                result += "3. TESTING RESOURCE ENDPOINT...\n"
                
                ServerManager.shared.executeServerCommand(command: "/resources", method: "GET", waitTime: 3) { resourceResult in
                    DispatchQueue.main.async {
                        switch resourceResult {
                        case .success(let response):
                            result += "   Resources Endpoint: ✓ Working\n"
                            if let dict = response as? [String: Any] {
                                result += "   CPU: \(dict["cpu"] ?? "N/A")\n"
                                result += "   Memory: \(dict["memory"] ?? "N/A")\n"
                                result += "   Disk: \(dict["disk"] ?? "N/A")\n\n"
                            }
                        case .failure(let error):
                            result += "   Resources Endpoint: ✗ Failed\n"
                            result += "   Error: \(error.localizedDescription)\n\n"
                        }
                        
                        result += "4. TESTING LOGS ENDPOINT...\n"
                        
                        ServerManager.shared.executeServerCommand(command: "/get_logs", method: "GET", waitTime: 5) { logsResult in
                            DispatchQueue.main.async {
                                switch logsResult {
                                case .success(let response):
                                    result += "   Logs Endpoint: ✓ Working\n"
                                    if let array = response as? [[String: Any]] {
                                        result += "   Log Count: \(array.count)\n"
                                    }
                                case .failure(let error):
                                    result += "   Logs Endpoint: ✗ Failed\n"
                                    result += "   Error: \(error.localizedDescription)\n"
                                }
                                
                                result += "\n=== END OF DIAGNOSTICS ===\n"
                                result += "\nIf you see errors above, please check:\n"
                                result += "- Server is running and accessible\n"
                                result += "- Credentials are correct\n"
                                result += "- Network connection is stable\n"
                                result += "- Firewall/router settings allow connection"
                                
                                self.diagnosticsResult = result
                                self.isRunningDiagnostics = false
                                self.showingDiagnostics = true
                            }
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    TroubleshootView()
}
