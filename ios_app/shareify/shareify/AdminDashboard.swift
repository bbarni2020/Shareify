//
//  AdminDashboard.swift
//  shareify
//
//  Created by Balogh Barnabás on 2025. 10. 04..
//

import SwiftUI
import Combine

struct AdminDashboard: View {
    @StateObject private var viewModel = AdminDashboardViewModel()
    @Environment(\.dismiss) private var dismiss
    @Environment(\.openURL) private var openURL
    @State private var isShowingPasswordSheet = false
    @State private var dashboardPasswordDraft = ""
    @FocusState private var passwordFieldFocused: Bool
    private let autoRefreshTimer = Timer.publish(every: 30, on: .main, in: .common).autoconnect()
    private let contentMaxWidth: CGFloat = 960

    var body: some View {
        ZStack {
            dashboardBackground
            VStack(spacing: 0) {
                ScrollView {
                    VStack(spacing: 24) {
                        metricsSection
                        controlsSection
                    }
                    .frame(maxWidth: contentMaxWidth, alignment: .center)
                    .padding(.horizontal, 24)
                    .padding(.top, 28)
                    .padding(.bottom, 40)
                    .frame(maxWidth: .infinity)
                }
                .scrollIndicators(.hidden)
            }
            .frame(maxWidth: .infinity, alignment: .top)
            .overlay(alignment: .top) {
                if let banner = viewModel.banner {
                    DashboardBannerView(banner: banner)
                        .padding(.top, 12)
                        .transition(.move(edge: .top).combined(with: .opacity))
                }
            }
        }
        .ignoresSafeArea(edges: [.top, .bottom])
        .task {
            viewModel.refresh()
        }
        .onReceive(autoRefreshTimer) { _ in
            viewModel.refresh()
        }
        .onChange(of: viewModel.requiresPasswordEntry) { _, needsPassword in
            if needsPassword {
                dashboardPasswordDraft = viewModel.storedPassword ?? ""
                isShowingPasswordSheet = true
            }
        }
        .sheet(isPresented: $isShowingPasswordSheet) {
            passwordCaptureSheet
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button("← Back") {
                    dismiss()
                }
                .foregroundColor(.white)
                .font(.system(size: 16, weight: .medium))
            }
        }
    }

    private var dashboardBackground: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(red: 0.05, green: 0.07, blue: 0.18),
                    Color(red: 0.01, green: 0.07, blue: 0.24)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            Circle()
                .fill(Color(red: 0.29, green: 0.37, blue: 0.94).opacity(0.32))
                .frame(width: 420, height: 420)
                .blur(radius: 120)
                .offset(x: 160, y: -260)

            Circle()
                .fill(Color(red: 0.11, green: 0.96, blue: 0.68).opacity(0.28))
                .frame(width: 420, height: 420)
                .blur(radius: 130)
                .offset(x: -200, y: 260)
        }
    }

    private var metricsSection: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Text("Bridge Metrics")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.white)
                Spacer()
                Button {
                    viewModel.refresh(forceLogin: false)
                } label: {
                    HStack(spacing: 8) {
                        if viewModel.isLoading {
                            ProgressView()
                                .progressViewStyle(.circular)
                                .tint(.white)
                                .scaleEffect(0.7)
                        }
                        Text(viewModel.isLoading ? "Refreshing…" : "Refresh Now")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.white)
                    }
                    .padding(.vertical, 10)
                    .padding(.horizontal, 16)
                    .background(Color.white.opacity(0.12), in: Capsule())
                }
                .disabled(viewModel.isLoading)
            }

            LazyVGrid(columns: metricsColumns, spacing: 16) {
                MetricCard(title: "Live Servers", value: viewModel.servers.count, subtitle: viewModel.serversTrendText, accent: Color(red: 0.45, green: 0.69, blue: 1.0))
                MetricCard(title: "Known Users", value: viewModel.knownUsersCount, subtitle: viewModel.usersTrendText, accent: Color(red: 0.6, green: 0.87, blue: 0.47))
                MetricCard(title: "Active Links", value: viewModel.activeLinkCount, subtitle: viewModel.activeTrendText, accent: Color(red: 1.0, green: 0.66, blue: 0.55))
            }

            Text("Service Health Probes")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.white.opacity(0.7))
                .padding(.top, 6)

            LazyVGrid(columns: endpointColumns, spacing: 16) {
                EndpointStatusCard(
                    name: "command.bbarni.hackclub.app",
                    expectation: "Expecting HTTP 405",
                    state: viewModel.commandServiceStatus
                )

                EndpointStatusCard(
                    name: "bridge.bbarni.hackclub.app",
                    expectation: "Expecting HTTP 200",
                    state: viewModel.bridgeServiceStatus
                )
            }
        }
    }

    private var controlsSection: some View {
        VStack(spacing: 24) {
            AdaptivePanel {
                header(title: "Connected Servers", subtitle: "Status matrix updates every 30 seconds")
                if viewModel.servers.isEmpty {
                    EmptyDashboardState(message: "No active bridge connections right now.")
                        .frame(minHeight: 160)
                } else {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 280), spacing: 18, alignment: .top)], spacing: 18) {
                        ForEach(viewModel.servers) { server in
                            ServerCard(server: server, isDisconnecting: viewModel.disconnecting.contains(server.id)) {
                                viewModel.disconnect(server: server)
                            }
                        }
                    }
                }
            }

            AdaptivePanel {
                header(title: "Bridge Activity Stream", subtitle: "Recent session touchpoints")
                if viewModel.activityServers.isEmpty {
                    EmptyDashboardState(message: "Activity stream populates once servers connect.")
                        .frame(minHeight: 140)
                } else {
                    VStack(spacing: 12) {
                        ForEach(viewModel.activityServers) { server in
                            ActivityRow(server: server)
                        }
                    }
                }
            }

            AdaptivePanel(extraPadding: true) {
                header(title: "Data Control Center", subtitle: "Secure management for relational and document stores")
                LazyVGrid(columns: databaseColumns, spacing: 18) {
                    DatabaseCard(icon: "🧬", title: "SQLite Core Console", description: "Browse structured credentials, execute live queries, and fine-tune access data with instant propagation across the bridge.") {
                        openURLIfPossible(path: "/dashboard/database/sqlite")
                    }
                    DatabaseCard(icon: "🪄", title: "JSON Directory", description: "Manipulate bridge metadata with schema hints, visualize raw payloads, and validate structures before committing changes.") {
                        openURLIfPossible(path: "/dashboard/database/json")
                    }
                }
                .padding(.top, 10)
            }
        }
    }

    private var metricsColumns: [GridItem] {
        [GridItem(.adaptive(minimum: 220), spacing: 16, alignment: .top)]
    }

    private var endpointColumns: [GridItem] {
        [GridItem(.adaptive(minimum: 260), spacing: 16, alignment: .top)]
    }

    private var databaseColumns: [GridItem] {
        [GridItem(.adaptive(minimum: 240), spacing: 18, alignment: .top)]
    }

    @ViewBuilder
    private func header(title: String, subtitle: String) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.white)
                Text(subtitle)
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(.white.opacity(0.55))
            }
            Spacer()
        }
    }

    private var passwordCaptureSheet: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Text("Admin Dashboard Password")
                    .font(.system(size: 20, weight: .semibold))
                    .padding(.top, 24)

                Text("Enter the password used for the Shareify cloud dashboard.")
                    .font(.system(size: 15))
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                SecureField("Dashboard password", text: $dashboardPasswordDraft)
                    .textContentType(.password)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 14))
                    .focused($passwordFieldFocused)
                    .padding(.horizontal, 24)

                HStack(spacing: 16) {
                    Button("Cancel") {
                        isShowingPasswordSheet = false
                        viewModel.clearStoredPassword()
                        dismiss()
                    }
                    .frame(maxWidth: .infinity)

                    Button("Save & Continue") {
                        let trimmed = dashboardPasswordDraft.trimmingCharacters(in: .whitespacesAndNewlines)
                        viewModel.updateStoredPassword(trimmed)
                        isShowingPasswordSheet = false
                        viewModel.refresh(forceLogin: true)
                    }
                    .disabled(dashboardPasswordDraft.isEmpty)
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .padding(.horizontal, 24)

                Spacer()
            }
            .navigationTitle("")
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Done") { passwordFieldFocused = false }
                }
            }
            .onAppear {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.45) {
                    passwordFieldFocused = true
                }
            }
        }
    }

    private func openURLIfPossible(path: String) {
        guard let url = viewModel.makeDashboardURL(path: path) else { return }
        openURL(url)
    }

}

private struct AdaptivePanel<Content: View>: View {
    let extraPadding: Bool
    @ViewBuilder let content: Content

    init(extraPadding: Bool = false, @ViewBuilder content: () -> Content) {
        self.extraPadding = extraPadding
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: extraPadding ? 20 : 16) {
            content
        }
        .padding(.horizontal, extraPadding ? 26 : 22)
        .padding(.vertical, extraPadding ? 26 : 22)
        .background(Color.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 28))
        .overlay(
            RoundedRectangle(cornerRadius: 28)
                .stroke(Color.white.opacity(0.12), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.22), radius: 18, x: 0, y: 12)
    }
}

private struct MetricCard: View {
    let title: String
    let value: Int
    let subtitle: String
    let accent: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title.uppercased())
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(.white.opacity(0.65))
                .tracking(1.1)

            HStack(alignment: .lastTextBaseline, spacing: 8) {
                Text("\(value)")
                    .font(.system(size: 32, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                Circle()
                    .fill(accent.opacity(0.7))
                    .frame(width: 10, height: 10)
            }

            Text(subtitle)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(accent.opacity(0.8))
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 18)
        .background(
            LinearGradient(
                colors: [accent.opacity(0.25), Color.white.opacity(0.08)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            in: RoundedRectangle(cornerRadius: 22)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 22)
                .stroke(Color.white.opacity(0.12), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(0.18), radius: 14, x: 0, y: 8)
    }
}

private struct EndpointStatusCard: View {
    let name: String
    let expectation: String
    let state: EndpointState

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 12) {
                Image(systemName: iconName)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(accentColor)
                    .frame(width: 34, height: 34)
                    .background(accentColor.opacity(0.18), in: RoundedRectangle(cornerRadius: 12))

                VStack(alignment: .leading, spacing: 2) {
                    Text(name)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.white)
                        .lineLimit(2)
                    Text(statusTitle)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(accentColor)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(accentColor.opacity(0.18), in: Capsule())
                }
            }

            VStack(alignment: .leading, spacing: 6) {
                Text(detailText)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.white.opacity(0.78))
                    .fixedSize(horizontal: false, vertical: true)
                Text(expectation)
                    .font(.system(size: 11, weight: .regular))
                    .foregroundColor(.white.opacity(0.45))
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 22))
        .overlay(
            RoundedRectangle(cornerRadius: 22)
                .stroke(Color.white.opacity(0.1), lineWidth: 1)
        )
    }

    private var accentColor: Color {
        switch state {
        case .loading:
            return Color.yellow
        case .up:
            return Color(red: 0.37, green: 0.87, blue: 0.66)
        case .down:
            return Color(red: 1.0, green: 0.48, blue: 0.56)
        }
    }

    private var statusTitle: String {
        switch state {
        case .loading:
            return "Checking"
        case .up:
            return "Online"
        case .down:
            return "Unavailable"
        }
    }

    private var detailText: String {
        switch state {
        case .loading:
            return "Pinging…"
        case .up:
            return "Responded as expected."
        case .down(let message):
            return "Last response: \(message)"
        }
    }

    private var iconName: String {
        switch state {
        case .loading:
            return "waveform.path"
        case .up:
            return "antenna.radiowaves.left.and.right"
        case .down:
            return "exclamationmark.triangle.fill"
        }
    }
}

private struct ServerCard: View {
    let server: AdminDashboardServer
    let isDisconnecting: Bool
    let disconnectAction: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(server.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.white)
                    Text(server.statusLabel)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color.green.opacity(0.7))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 4)
                        .background(Color.green.opacity(0.12), in: Capsule())
                }

                Spacer()

                Button {
                    disconnectAction()
                } label: {
                    Text(isDisconnecting ? "Disconnecting…" : "Disconnect")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(Color(red: 1.0, green: 0.71, blue: 0.76))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.red.opacity(0.18), in: Capsule())
                }
                .disabled(isDisconnecting)
                .opacity(isDisconnecting ? 0.6 : 1.0)
            }

            VStack(alignment: .leading, spacing: 8) {
                LabeledDetailView(label: "Connected", value: server.connectedDisplay)
                LabeledDetailView(label: "Last Seen", value: server.lastSeenDisplay)
                LabeledDetailView(label: "Auth Token", value: server.authTokenDisplay)
            }
        }
        .padding(20)
        .background(Color(red: 0.04, green: 0.1, blue: 0.24).opacity(0.65), in: RoundedRectangle(cornerRadius: 22))
        .overlay(
            RoundedRectangle(cornerRadius: 22)
                .stroke(Color.white.opacity(0.08), lineWidth: 1)
        )
    }
}

private struct ActivityRow: View {
    let server: AdminDashboardServer

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(server.name)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.white)
                Spacer()
                Text(server.idPrefix)
                    .font(.system(size: 12, weight: .medium, design: .monospaced))
                    .foregroundColor(.white.opacity(0.55))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.white.opacity(0.08), in: Capsule())
            }

            HStack(spacing: 12) {
                Label(server.lastSeenRelative, systemImage: "clock")
                Label(server.pendingCommandsDisplay, systemImage: "arrow.triangle.2.circlepath")
            }
            .font(.system(size: 13, weight: .medium))
            .foregroundColor(.white.opacity(0.7))
        }
        .padding(18)
        .background(Color.white.opacity(0.05), in: RoundedRectangle(cornerRadius: 18))
    }
}

private struct DatabaseCard: View {
    let icon: String
    let title: String
    let description: String
    let action: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(icon)
                .font(.system(size: 26))
            Text(title)
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white)
            Text(description)
                .font(.system(size: 13))
                .foregroundColor(.white.opacity(0.65))
            Spacer(minLength: 0)
            Button(action: action) {
                Text("Open")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Color(red: 0.05, green: 0.07, blue: 0.18))
                    .padding(.vertical, 10)
                    .padding(.horizontal, 16)
                    .background(
                        LinearGradient(
                            colors: [Color(red: 0.7, green: 0.83, blue: 1.0), Color(red: 0.33, green: 0.66, blue: 0.98)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        in: Capsule()
                    )
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white.opacity(0.08), in: RoundedRectangle(cornerRadius: 22))
        .overlay(
            RoundedRectangle(cornerRadius: 22)
                .stroke(Color.white.opacity(0.1), lineWidth: 1)
        )
    }
}

private struct LabeledDetailView: View {
    let label: String
    let value: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text(label)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.white.opacity(0.6))
                .frame(width: 86, alignment: .leading)
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
        }
    }
}

private struct EmptyDashboardState: View {
    let message: String

    var body: some View {
        VStack(spacing: 14) {
            Image(systemName: "cloud.slash.fill")
                .font(.system(size: 28))
                .foregroundColor(.white.opacity(0.45))
            Text(message)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.white.opacity(0.65))
                .multilineTextAlignment(.center)
        }
        .padding(36)
        .frame(maxWidth: .infinity)
        .background(Color.white.opacity(0.05), in: RoundedRectangle(cornerRadius: 22))
    }
}

private struct DashboardBannerView: View {
    let banner: DashboardBanner

    var body: some View {
        VStack {
            HStack {
                Image(systemName: banner.iconName)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(banner.foregroundColor)
                Text(banner.message)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.white)
                Spacer()
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 12)
            .background(banner.backgroundColor, in: Capsule())
        }
        .padding(.horizontal, 24)
    }
}

struct AdminDashboard_Previews: PreviewProvider {
    static var previews: some View {
        AdminDashboard()
            .preferredColorScheme(.dark)
    }
}

final class AdminDashboardViewModel: ObservableObject {
    @Published var servers: [AdminDashboardServer] = []
    @Published var activityServers: [AdminDashboardServer] = []
    @Published var knownUsersCount: Int = 0
    @Published var activeLinkCount: Int = 0
    @Published var isLoading: Bool = false
    @Published var banner: DashboardBanner?
    @Published var requiresPasswordEntry: Bool = false
    @Published var isLoggingOut: Bool = false
    @Published var disconnecting: Set<String> = []
    @Published var commandServiceStatus: EndpointState = .loading
    @Published var bridgeServiceStatus: EndpointState = .loading

    private let baseURL = URL(string: "https://bridge.bbarni.hackclub.app")!
    private let commandProbeURL = URL(string: "https://command.bbarni.hackclub.app")!
    private let bridgeProbeURL = URL(string: "https://bridge.bbarni.hackclub.app")!
    private let defaults = UserDefaults.standard
    private let session: URLSession
    private var lastServerCount: Int = 0
    private var lastServerDelta: Int = 0

    init(session: URLSession = .shared) {
        self.session = session
    }

    var storedPassword: String? {
        defaults.string(forKey: "dashboard_password")
    }

    private var storedToken: String? {
        get { defaults.string(forKey: "dashboard_token") }
        set {
            defaults.setValue(newValue, forKey: "dashboard_token")
        }
    }

    var lastUpdatedText: String {
        if let last = lastUpdated {
            return DashboardDateHelper.shared.displayFormatter.string(from: last)
        }
        return "Synchronizing…"
    }

    var serversTrendText: String {
        if lastServerDelta > 0 {
            return "+\(lastServerDelta) new bridge link"
        } else if lastServerDelta < 0 {
            return "\(lastServerDelta) bridge link"
        }
        return "Stable mesh"
    }

    var usersTrendText: String {
        knownUsersCount == 0 ? "No identities yet" : "Directory hydrated"
    }

    var activeTrendText: String {
        if lastServerDelta > 0 {
            return "Topology expanding"
        } else if lastServerDelta < 0 {
            return "Some connections closed"
        } else if servers.count > 0 {
            return "Monitoring continuity"
        } else {
            return "Monitoring"
        }
    }

    private(set) var lastUpdated: Date?

    func refresh(forceLogin: Bool) {
        guard !isLoading else {
            refreshServiceStatuses()
            return
        }
        isLoading = true
        refreshServiceStatuses()
        if forceLogin {
            invalidateToken()
        }
        ensureToken { [weak self] result in
            guard let self else { return }
            switch result {
            case .success(let token):
                self.fetchDashboardData(using: token, allowRetry: true)
            case .failure(let error):
                DispatchQueue.main.async {
                    self.isLoading = false
                    if case DashboardError.passwordMissing = error {
                        self.requiresPasswordEntry = true
                    } else {
                        self.show(error: error)
                    }
                }
            }
        }
    }

    func refresh() {
        refresh(forceLogin: false)
    }

    func refreshServiceStatuses() {
        commandServiceStatus = .loading
        bridgeServiceStatus = .loading

        runHealthCheck(url: commandProbeURL, expecting: 405) { [weak self] state in
            DispatchQueue.main.async {
                self?.commandServiceStatus = state
            }
        }

        runHealthCheck(url: bridgeProbeURL, expecting: 200) { [weak self] state in
            DispatchQueue.main.async {
                self?.bridgeServiceStatus = state
            }
        }
    }

    func updateStoredPassword(_ password: String) {
        defaults.setValue(password, forKey: "dashboard_password")
        defaults.synchronize()
        requiresPasswordEntry = false
    }

    func clearStoredPassword() {
        defaults.removeObject(forKey: "dashboard_password")
        defaults.removeObject(forKey: "dashboard_token")
        defaults.synchronize()
        requiresPasswordEntry = true
    }

    func makeDashboardURL(path: String) -> URL? {
        URL(string: path, relativeTo: baseURL)
    }

    func disconnect(server: AdminDashboardServer) {
        guard !disconnecting.contains(server.id) else { return }
        guard let token = storedToken else {
            show(error: DashboardError.passwordMissing)
            requiresPasswordEntry = true
            return
        }

        disconnecting.insert(server.id)
        guard let url = URL(string: "/dashboard/servers/\(server.id)/disconnect", relativeTo: baseURL) else {
            disconnecting.remove(server.id)
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("dashboard_token=\(token)", forHTTPHeaderField: "Cookie")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        session.dataTask(with: request) { [weak self] data, response, error in
            guard let self else { return }
            DispatchQueue.main.async {
                self.disconnecting.remove(server.id)
            }

            if let error = error {
                self.show(error: .network(error))
                return
            }

            guard let http = response as? HTTPURLResponse else {
                self.show(error: .invalidResponse)
                return
            }

            if http.statusCode == 401 {
                self.handleUnauthorized()
                return
            }

            guard http.statusCode == 200 else {
                let message = self.message(from: data) ?? "Unable to disconnect"
                self.show(error: .message(message))
                return
            }

            self.showBanner(message: "Server disconnected", tone: .success)
            self.refresh(forceLogin: false)
        }.resume()
    }

    func logout(completion: @escaping (Bool) -> Void) {
        guard !isLoggingOut else { return }
        guard let token = storedToken else {
            clearStoredPassword()
            completion(true)
            return
        }

        guard let url = URL(string: "/dashboard/logout", relativeTo: baseURL) else {
            completion(false)
            return
        }

        isLoggingOut = true
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("dashboard_token=\(token)", forHTTPHeaderField: "Cookie")

        session.dataTask(with: request) { [weak self] _, _, _ in
            guard let self else { return }
            DispatchQueue.main.async {
                self.isLoggingOut = false
                self.invalidateToken()
                completion(true)
            }
        }.resume()
    }

    private func ensureToken(completion: @escaping (Result<String, DashboardError>) -> Void) {
        if let token = storedToken, !token.isEmpty {
            completion(.success(token))
            return
        }

        guard let password = storedPassword, !password.isEmpty else {
            completion(.failure(.passwordMissing))
            return
        }

        loginWithDashboardPassword(password: password, completion: completion)
    }

    private func loginWithDashboardPassword(password: String, completion: @escaping (Result<String, DashboardError>) -> Void) {
        guard let url = URL(string: "/dashboard/login", relativeTo: baseURL) else {
            completion(.failure(.invalidResponse))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try? JSONSerialization.data(withJSONObject: ["password": password])

        session.dataTask(with: request) { [weak self] data, response, error in
            guard let self else { return }
            if let error = error {
                completion(.failure(.network(error)))
                return
            }

            guard let http = response as? HTTPURLResponse else {
                completion(.failure(.invalidResponse))
                return
            }

            guard http.statusCode == 200, let data else {
                let message = self.message(from: data) ?? "Dashboard login failed"
                completion(.failure(.message(message)))
                return
            }

            guard
                let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                let token = json["token"] as? String
            else {
                completion(.failure(.invalidResponse))
                return
            }

            self.storedToken = token
            completion(.success(token))
        }.resume()
    }

    private func fetchDashboardData(using token: String, allowRetry: Bool) {
        let group = DispatchGroup()
        var fetchedServers: Result<[AdminDashboardServer], DashboardError> = .failure(.invalidResponse)
        var fetchedUsers: Result<Int, DashboardError> = .failure(.invalidResponse)

        group.enter()
        fetchServers(token: token) { result in
            fetchedServers = result
            group.leave()
        }

        group.enter()
        fetchKnownUsers(token: token) { result in
            fetchedUsers = result
            group.leave()
        }

        group.notify(queue: .main) {
            self.isLoading = false

            if case .success(let servers) = fetchedServers {
                let previousCount = self.lastServerCount
                self.lastServerCount = servers.count
                self.lastServerDelta = servers.count - previousCount
                self.servers = servers
                self.activityServers = Array(servers.sorted(by: { ($0.lastSeen ?? .distantPast) > ($1.lastSeen ?? .distantPast) }).prefix(6))
                self.activeLinkCount = servers.count
            }

            if case .success(let count) = fetchedUsers {
                self.knownUsersCount = count
            }

            if case .failure(let error) = fetchedServers {
                if case .unauthorized = error, allowRetry {
                    self.handleUnauthorized()
                    return
                }
                self.show(error: error)
            }

            if case .failure(let error) = fetchedUsers {
                if case .unauthorized = error, allowRetry {
                    self.handleUnauthorized()
                    return
                }
                self.show(error: error)
            }

            self.lastUpdated = Date()
        }
    }

    private func fetchServers(token: String, completion: @escaping (Result<[AdminDashboardServer], DashboardError>) -> Void) {
        guard let url = URL(string: "/dashboard/servers", relativeTo: baseURL) else {
            completion(.failure(.invalidResponse))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("dashboard_token=\(token)", forHTTPHeaderField: "Cookie")

        session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(.network(error)))
                return
            }

            guard let http = response as? HTTPURLResponse else {
                completion(.failure(.invalidResponse))
                return
            }

            if http.statusCode == 401 {
                completion(.failure(.unauthorized))
                return
            }

            guard http.statusCode == 200, let data else {
                let message = self.message(from: data) ?? "Unable to load servers"
                completion(.failure(.message(message)))
                return
            }

            guard
                let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                let success = json["success"] as? Bool, success,
                let rawServers = json["servers"] as? [[String: Any]]
            else {
                completion(.failure(.invalidResponse))
                return
            }

            let servers = rawServers.compactMap { AdminDashboardServer(json: $0) }
            completion(.success(servers))
        }.resume()
    }

    private func fetchKnownUsers(token: String, completion: @escaping (Result<Int, DashboardError>) -> Void) {
        guard let url = URL(string: "/dashboard/database/json/data", relativeTo: baseURL) else {
            completion(.failure(.invalidResponse))
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("dashboard_token=\(token)", forHTTPHeaderField: "Cookie")

        session.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(.network(error)))
                return
            }

            guard let http = response as? HTTPURLResponse else {
                completion(.failure(.invalidResponse))
                return
            }

            if http.statusCode == 401 {
                completion(.failure(.unauthorized))
                return
            }

            guard http.statusCode == 200, let data else {
                let message = self.message(from: data) ?? "Unable to load directory data"
                completion(.failure(.message(message)))
                return
            }

            guard
                let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                let success = json["success"] as? Bool, success,
                let dataDict = json["data"] as? [String: Any]
            else {
                completion(.failure(.invalidResponse))
                return
            }

            completion(.success(dataDict.keys.count))
        }.resume()
    }

    private func handleUnauthorized() {
        invalidateToken()
        DispatchQueue.main.async {
            self.requiresPasswordEntry = true
            self.showBanner(message: "Dashboard session expired", tone: .warning)
        }
    }

    private func invalidateToken() {
        defaults.removeObject(forKey: "dashboard_token")
        defaults.synchronize()
    }

    private func show(error: DashboardError) {
        let message: String
        switch error {
        case .passwordMissing:
            message = "Dashboard password required"
        case .unauthorized:
            message = "Unauthorized. Please re-authenticate."
        case .invalidResponse:
            message = "Unexpected dashboard response"
        case .message(let custom):
            message = custom
        case .network(let err):
            message = err.localizedDescription
        }
        showBanner(message: message, tone: .error)
    }

    private func showBanner(message: String, tone: DashboardBanner.Tone) {
        DispatchQueue.main.async {
            let banner = DashboardBanner(message: message, tone: tone)
            self.banner = banner
            DispatchQueue.main.asyncAfter(deadline: .now() + 4.0) {
                if self.banner?.id == banner.id {
                    self.banner = nil
                }
            }
        }
    }

    private func message(from data: Data?) -> String? {
        guard
            let data,
            let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let message = json["error"] as? String
        else {
            return nil
        }
        return message
    }

    private func runHealthCheck(url: URL, expecting statusCode: Int, completion: @escaping (EndpointState) -> Void) {
        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.timeoutInterval = 8

        session.dataTask(with: request) { _, response, error in
            if let error {
                completion(.down("\(error.localizedDescription)"))
                return
            }

            guard let http = response as? HTTPURLResponse else {
                completion(.down("No HTTP response"))
                return
            }

            if http.statusCode == statusCode {
                completion(.up)
            } else {
                completion(.down("HTTP \(http.statusCode)"))
            }
        }.resume()
    }
}

struct AdminDashboardServer: Identifiable, Hashable {
    let id: String
    let name: String
    let connectedAt: Date?
    let connectedRaw: String?
    let lastSeen: Date?
    let lastSeenRaw: String?
    let authToken: String?
    let pendingCommands: Int?

    init?(json: [String: Any]) {
        guard let id = json["id"] as? String else { return nil }
        self.id = id
        self.name = (json["name"] as? String)?.trimmingCharacters(in: .whitespacesAndNewlines).nonEmpty ?? "Server \(id.prefix(6))"

        if let connectedString = json["connected_at"] as? String, !connectedString.isEmpty {
            self.connectedAt = DashboardDateHelper.shared.parse(from: connectedString)
            self.connectedRaw = connectedString
        } else {
            self.connectedAt = nil
            self.connectedRaw = nil
        }

        if let lastSeenString = json["last_seen"] as? String, !lastSeenString.isEmpty {
            self.lastSeen = DashboardDateHelper.shared.parse(from: lastSeenString)
            self.lastSeenRaw = lastSeenString
        } else {
            self.lastSeen = nil
            self.lastSeenRaw = nil
        }

        self.authToken = json["auth_token"] as? String
        if let pending = json["pending_commands"] as? Int {
            self.pendingCommands = pending
        } else if let pendingString = json["pending_commands"] as? String, let value = Int(pendingString) {
            self.pendingCommands = value
        } else {
            self.pendingCommands = nil
        }
    }

    var connectedDisplay: String {
        if let connectedAt {
            return DashboardDateHelper.shared.relativeFormatter.localizedString(for: connectedAt, relativeTo: Date())
        }
        return connectedRaw ?? "Unknown"
    }

    var lastSeenDisplay: String {
        if let lastSeen {
            return DashboardDateHelper.shared.relativeFormatter.localizedString(for: lastSeen, relativeTo: Date())
        }
        return lastSeenRaw ?? "Unknown"
    }

    var authTokenDisplay: String {
        guard let authToken, !authToken.isEmpty else { return "Unavailable" }
        if authToken.count <= 10 { return authToken }
        let start = authToken.prefix(6)
        let end = authToken.suffix(4)
        return "\(start)…\(end)"
    }

    var idPrefix: String {
        String(id.prefix(10)) + (id.count > 10 ? "…" : "")
    }

    var lastSeenRelative: String {
        if let lastSeen {
            return DashboardDateHelper.shared.relativeFormatter.localizedString(for: lastSeen, relativeTo: Date())
        }
        return "Last ping unknown"
    }

    var pendingCommandsDisplay: String {
        if let pendingCommands {
            return "\(pendingCommands) pending commands"
        }
        return "0 pending commands"
    }

    var statusLabel: String {
        "Online"
    }
}

struct DashboardBanner: Identifiable {
    enum Tone {
        case success
        case warning
        case error
    }

    let id = UUID()
    let message: String
    let tone: Tone

    var iconName: String {
        switch tone {
        case .success: return "checkmark.circle.fill"
        case .warning: return "exclamationmark.triangle.fill"
        case .error: return "xmark.octagon.fill"
        }
    }

    var backgroundColor: Color {
        switch tone {
        case .success: return Color.green.opacity(0.28)
        case .warning: return Color.orange.opacity(0.3)
        case .error: return Color.red.opacity(0.32)
        }
    }

    var foregroundColor: Color {
        switch tone {
        case .success: return Color.green
        case .warning: return Color.orange
        case .error: return Color.red
        }
    }
}

enum EndpointState: Equatable {
    case loading
    case up
    case down(String)
}

private enum DashboardError: Error {
    case passwordMissing
    case unauthorized
    case invalidResponse
    case message(String)
    case network(Error)
}

final class DashboardDateHelper {
    static let shared = DashboardDateHelper()

    private let isoFormatter: ISO8601DateFormatter
    private let legacyFormatter: DateFormatter
    let displayFormatter: DateFormatter
    let relativeFormatter: RelativeDateTimeFormatter

    private init() {
        isoFormatter = ISO8601DateFormatter()
        isoFormatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

        legacyFormatter = DateFormatter()
        legacyFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        legacyFormatter.timeZone = TimeZone(secondsFromGMT: 0)

        displayFormatter = DateFormatter()
        displayFormatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        displayFormatter.timeZone = .current

        relativeFormatter = RelativeDateTimeFormatter()
        relativeFormatter.unitsStyle = .short
    }

    func parse(from raw: String) -> Date? {
        if raw.lowercased() == "unknown" { return nil }
        if let iso = isoFormatter.date(from: raw) {
            return iso
        }
        if let legacy = legacyFormatter.date(from: raw) {
            return legacy
        }
        return nil
    }
}

private extension String {
    var nonEmpty: String? {
        isEmpty ? nil : self
    }
}
