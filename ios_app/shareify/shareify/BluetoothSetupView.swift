import SwiftUI
import CoreBluetooth

struct BluetoothSetupView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var bluetoothManager = BluetoothSetupManager()
    @StateObject private var backgroundManager = BackgroundManager.shared
    @State private var cardOpacity: Double = 0
    @State private var cardOffset: CGFloat = 50
    @State private var showingSuccess = false
    @State private var showingError = false
    @State private var errorMessage = ""
    @State private var navigateToLogin = false
    
    var body: some View {
        if navigateToLogin {
            Login()
        } else {
            setupView
                .onAppear {
                    startAnimation()
                    bluetoothManager.startScanning()
                }
                .onDisappear {
                    bluetoothManager.stopScanning()
                }
        }
    }
    
    private var setupView: some View {
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
                            Text("Bluetooth Setup")
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
                    .opacity(cardOpacity)
                    .offset(y: cardOffset)
                    .ignoresSafeArea(.all, edges: [.bottom, .leading, .trailing])
                    .overlay(
                        setupContentView(geometry: geometry)
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
        .overlay(
            Group {
                if showingSuccess {
                    successOverlay
                        .transition(.opacity.combined(with: .scale))
                }
            }
        )
        .alert("Connection Error", isPresented: $showingError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(errorMessage)
        }
    }
    
    private func setupContentView(geometry: GeometryProxy) -> some View {
        ScrollView {
            VStack(spacing: 30) {
                VStack(spacing: 20) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    gradient: Gradient(colors: [
                                        Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255).opacity(0.15),
                                        Color(red: 0x29/255, green: 0x6D/255, blue: 0xE0/255).opacity(0.15)
                                    ]),
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 100, height: 100)
                        
                        Image(systemName: bluetoothManager.isScanning ? "antenna.radiowaves.left.and.right" : "server.rack")
                            .font(.system(size: 40, weight: .medium))
                            .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                            .symbolEffect(.variableColor.iterative, isActive: bluetoothManager.isScanning)
                    }
                    
                    Text("Setup Shareify Server")
                        .font(.system(size: 28, weight: .bold))
                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    
                    Text("Configure a new Shareify server via Bluetooth connection")
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 20)
                }
                .padding(.top, 30)
                
                if bluetoothManager.bluetoothState == .poweredOff {
                    statusCard(
                        icon: "exclamationmark.triangle.fill",
                        title: "Bluetooth Disabled",
                        description: "Enable Bluetooth in Settings to discover servers",
                        color: .orange
                    )
                } else if bluetoothManager.bluetoothState == .unauthorized {
                    statusCard(
                        icon: "lock.fill",
                        title: "Permission Required",
                        description: "Grant Bluetooth access in Settings to continue",
                        color: .red
                    )
                } else if bluetoothManager.isScanning {
                    VStack(spacing: 15) {
                        HStack {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255)))
                                .scaleEffect(0.9)
                            Text("Scanning for servers...")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                        }
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(
                            RoundedRectangle(cornerRadius: 15)
                                .fill(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255).opacity(0.1))
                        )
                        .overlay(
                            RoundedRectangle(cornerRadius: 15)
                                .stroke(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255).opacity(0.3), lineWidth: 1)
                        )
                    }
                    .padding(.horizontal, 20)
                }
                
                if !bluetoothManager.discoveredServers.isEmpty {
                    VStack(alignment: .leading, spacing: 15) {
                        Text("Available Servers")
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                            .padding(.horizontal, 20)
                        
                        ForEach(bluetoothManager.discoveredServers, id: \.identifier) { peripheral in
                            serverCard(peripheral: peripheral)
                        }
                    }
                }
                
                if bluetoothManager.connectedPeripheral != nil {
                    setupFormView
                }
                
                Spacer(minLength: 30)
            }
        }
    }
    
    private var setupFormView: some View {
        VStack(alignment: .leading, spacing: 25) {
            Text("Server Configuration")
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                .padding(.horizontal, 20)
            
            VStack(spacing: 20) {
                if bluetoothManager.setupStep == .selectingPath || bluetoothManager.setupStep == .completed {
                    pathSelectionView
                }
                
                if bluetoothManager.setupStep == .settingPassword || bluetoothManager.setupStep == .completed {
                    passwordFieldsView
                }
                
                if bluetoothManager.setupStep == .settingSudoPassword || bluetoothManager.setupStep == .completed {
                    sudoPasswordFieldView
                }
                
                if bluetoothManager.setupStep == .completed {
                    completeButton
                }
            }
            .padding(20)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
            .colorScheme(.light)
            .padding(.horizontal, 20)
        }
    }
    
    private var pathSelectionView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "folder.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255))
                Text("Server Path")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            HStack {
                Text(bluetoothManager.selectedPath.isEmpty ? "Not selected" : bluetoothManager.selectedPath)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                    .lineLimit(1)
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255).opacity(0.5))
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color.white.opacity(0.6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(Color(red: 0xE5/255, green: 0xE7/255, blue: 0xEB/255), lineWidth: 1.5)
                    )
            )
            .onTapGesture {
                bluetoothManager.showPathPicker = true
            }
            
            if bluetoothManager.selectedPath.isEmpty {
                Button(action: {
                    bluetoothManager.sendPathToServer()
                }) {
                    Text("Select Path")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(
                            RoundedRectangle(cornerRadius: 12)
                                .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                        )
                }
                .disabled(bluetoothManager.selectedPath.isEmpty)
                .opacity(bluetoothManager.selectedPath.isEmpty ? 0.6 : 1.0)
            }
        }
        .sheet(isPresented: $bluetoothManager.showPathPicker) {
            PathPickerView(bluetoothManager: bluetoothManager)
        }
    }
    
    private var passwordFieldsView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "lock.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255))
                Text("Admin Password")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            SecureField("Enter password", text: $bluetoothManager.password)
                .textFieldStyle(CustomTextFieldStyle())
                .frame(height: 50)
            
            if !bluetoothManager.password.isEmpty {
                Button(action: {
                    bluetoothManager.sendPasswordToServer()
                }) {
                    HStack {
                        if bluetoothManager.isSendingData {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(0.8)
                        } else {
                            Text("Set Password")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.white)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                    )
                }
                .disabled(bluetoothManager.isSendingData || bluetoothManager.password.count < 6)
                .opacity(bluetoothManager.password.count < 6 ? 0.6 : 1.0)
            }
            
            if bluetoothManager.password.count > 0 && bluetoothManager.password.count < 6 {
                Text("Password must be at least 6 characters")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.red)
            }
        }
    }
    
    private var sudoPasswordFieldView: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "key.fill")
                    .font(.system(size: 16))
                    .foregroundColor(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255))
                Text("Communication Password")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            Text("This password is used for secure communication between clients")
                .font(.system(size: 12, weight: .regular))
                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255).opacity(0.8))
            
            SecureField("Enter communication password", text: $bluetoothManager.sudoPassword)
                .textFieldStyle(CustomTextFieldStyle())
                .frame(height: 50)
            
            if !bluetoothManager.sudoPassword.isEmpty {
                Button(action: {
                    bluetoothManager.sendSudoPasswordToServer()
                }) {
                    HStack {
                        if bluetoothManager.isSendingData {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(0.8)
                        } else {
                            Text("Set Communication Password")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.white)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                    )
                }
                .disabled(bluetoothManager.isSendingData || bluetoothManager.sudoPassword.count < 6)
                .opacity(bluetoothManager.sudoPassword.count < 6 ? 0.6 : 1.0)
            }
            
            if bluetoothManager.sudoPassword.count > 0 && bluetoothManager.sudoPassword.count < 6 {
                Text("Password must be at least 6 characters")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.red)
            }
        }
    }
    
    private var completeButton: some View {
        VStack(spacing: 15) {
            Button(action: {
                bluetoothManager.completeSetup()
                showingSuccess = true
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
                    withAnimation(.easeInOut(duration: 0.5)) {
                        navigateToLogin = true
                    }
                }
            }) {
                HStack {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 18))
                    Text("Complete Setup")
                        .font(.system(size: 18, weight: .bold))
                }
                .foregroundColor(.white)
                .frame(maxWidth: .infinity)
                .frame(height: 55)
                .background(
                    LinearGradient(
                        gradient: Gradient(colors: [
                            Color(red: 0x22/255, green: 0xC5/255, blue: 0x5E/255),
                            Color(red: 0x16/255, green: 0xA3/255, blue: 0x4A/255)
                        ]),
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .cornerRadius(15)
                .shadow(color: Color(red: 0x22/255, green: 0xC5/255, blue: 0x5E/255).opacity(0.4), radius: 10, x: 0, y: 5)
            }
            
            Text("The server will start after completion")
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
        }
    }
    
    private func serverCard(peripheral: CBPeripheral) -> some View {
        Button(action: {
            let impactFeedback = UIImpactFeedbackGenerator(style: .medium)
            impactFeedback.impactOccurred()
            bluetoothManager.connectToServer(peripheral)
        }) {
            HStack(spacing: 15) {
                ZStack {
                    Circle()
                        .fill(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255).opacity(0.15))
                        .frame(width: 50, height: 50)
                    
                    Image(systemName: bluetoothManager.isConnecting && bluetoothManager.connectingPeripheral?.identifier == peripheral.identifier ? "antenna.radiowaves.left.and.right" : "server.rack")
                        .font(.system(size: 22))
                        .foregroundColor(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255))
                }
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(peripheral.name ?? "Shareify Server")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    
                    Text("Tap to connect")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                }
                
                Spacer()
                
                if bluetoothManager.isConnecting && bluetoothManager.connectingPeripheral?.identifier == peripheral.identifier {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255)))
                        .scaleEffect(0.9)
                } else {
                    Image(systemName: "chevron.right")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255).opacity(0.4))
                }
            }
            .padding(18)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
            .colorScheme(.light)
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255).opacity(0.3), lineWidth: 1.5)
            )
            .shadow(color: .black.opacity(0.06), radius: 8, x: 0, y: 4)
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 20)
        .disabled(bluetoothManager.isConnecting)
    }
    
    private func statusCard(icon: String, title: String, description: String, color: Color) -> some View {
        VStack(spacing: 15) {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundColor(color)
            
            Text(title)
                .font(.system(size: 18, weight: .bold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            
            Text(description)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                .multilineTextAlignment(.center)
        }
        .padding(25)
        .frame(maxWidth: .infinity)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
        .colorScheme(.light)
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(color.opacity(0.3), lineWidth: 1.5)
        )
        .padding(.horizontal, 20)
    }
    
    private var successOverlay: some View {
        ZStack {
            Color.black.opacity(0.4)
                .ignoresSafeArea()
            
            VStack(spacing: 20) {
                ZStack {
                    Circle()
                        .fill(Color(red: 0x22/255, green: 0xC5/255, blue: 0x5E/255))
                        .frame(width: 80, height: 80)
                    
                    Image(systemName: "checkmark")
                        .font(.system(size: 40, weight: .bold))
                        .foregroundColor(.white)
                }
                
                Text("Setup Complete!")
                    .font(.system(size: 24, weight: .bold))
                    .foregroundColor(.white)
                
                Text("Your server is now ready")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.white.opacity(0.9))
            }
            .padding(40)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 30))
            .colorScheme(.dark)
        }
    }
    
    private func startAnimation() {
        withAnimation(.easeOut(duration: 0.8)) {
            cardOpacity = 1.0
            cardOffset = 0
        }
    }
}

struct PathPickerView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var bluetoothManager: BluetoothSetupManager
    @State private var currentPath: String = ""
    @State private var directories: [DirectoryItem] = []
    @State private var isLoading = false
    @State private var navigationStack: [String] = []
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                if isLoading {
                    ProgressView()
                        .scaleEffect(1.2)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    List {
                        if !navigationStack.isEmpty {
                            Button(action: navigateBack) {
                                HStack {
                                    Image(systemName: "arrow.up")
                                        .foregroundColor(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255))
                                    Text("Parent Folder")
                                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                }
                            }
                        }
                        
                        ForEach(directories, id: \.path) { directory in
                            Button(action: {
                                navigateToDirectory(directory.path)
                            }) {
                                HStack {
                                    Image(systemName: "folder.fill")
                                        .foregroundColor(Color(red: 0x3B/255, green: 0x82/255, blue: 0xF6/255))
                                    Text(directory.name)
                                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Select Path")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Select") {
                        bluetoothManager.selectedPath = currentPath.isEmpty ? "/" : currentPath
                        bluetoothManager.sendPathToServer()
                        dismiss()
                    }
                    .disabled(currentPath.isEmpty && navigationStack.isEmpty)
                }
            }
            .onAppear {
                loadInitialDirectories()
            }
        }
    }
    
    private func loadInitialDirectories() {
        isLoading = true
        bluetoothManager.requestDrives { drives in
            DispatchQueue.main.async {
                self.directories = drives
                self.isLoading = false
            }
        }
    }
    
    private func navigateToDirectory(_ path: String) {
        navigationStack.append(currentPath)
        currentPath = path
        isLoading = true
        
        bluetoothManager.requestDirectories(at: path) { dirs in
            DispatchQueue.main.async {
                self.directories = dirs
                self.isLoading = false
            }
        }
    }
    
    private func navigateBack() {
        guard !navigationStack.isEmpty else { return }
        currentPath = navigationStack.removeLast()
        
        if navigationStack.isEmpty {
            loadInitialDirectories()
        } else {
            isLoading = true
            bluetoothManager.requestDirectories(at: currentPath) { dirs in
                DispatchQueue.main.async {
                    self.directories = dirs
                    self.isLoading = false
                }
            }
        }
    }
}

struct DirectoryItem {
    let name: String
    let path: String
}

class BluetoothSetupManager: NSObject, ObservableObject, CBCentralManagerDelegate, CBPeripheralDelegate {
    @Published var discoveredServers: [CBPeripheral] = []
    @Published var isScanning = false
    @Published var isConnecting = false
    @Published var connectedPeripheral: CBPeripheral?
    @Published var connectingPeripheral: CBPeripheral?
    @Published var bluetoothState: CBManagerState = .unknown
    @Published var setupStep: SetupStep = .selectingPath
    @Published var selectedPath: String = ""
    @Published var password: String = ""
    @Published var sudoPassword: String = ""
    @Published var isSendingData = false
    @Published var showPathPicker = false
    
    private var centralManager: CBCentralManager?
    private var writeCharacteristic: CBCharacteristic?
    private let serviceUUID = CBUUID(string: "94f39d29-7d6d-437d-973b-fba39e49d4ee")
    private let characteristicUUID = CBUUID(string: "94f39d2a-7d6d-437d-973b-fba39e49d4ee")
    
    enum SetupStep {
        case selectingPath
        case settingPassword
        case settingSudoPassword
        case completed
    }
    
    override init() {
        super.init()
        centralManager = CBCentralManager(delegate: self, queue: nil)
    }
    
    func startScanning() {
        guard centralManager?.state == .poweredOn else { return }
        isScanning = true
        centralManager?.scanForPeripherals(withServices: [serviceUUID], options: nil)
    }
    
    func stopScanning() {
        isScanning = false
        centralManager?.stopScan()
    }
    
    func connectToServer(_ peripheral: CBPeripheral) {
        isConnecting = true
        connectingPeripheral = peripheral
        peripheral.delegate = self
        centralManager?.connect(peripheral, options: nil)
    }
    
    func sendPathToServer() {
        guard let peripheral = connectedPeripheral,
              let characteristic = writeCharacteristic else { return }
        
        let command = "SET_PATH:\(selectedPath)\n"
        if let data = command.data(using: .utf8) {
            isSendingData = true
            peripheral.writeValue(data, for: characteristic, type: .withResponse)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.isSendingData = false
                self.setupStep = .settingPassword
            }
        }
    }
    
    func sendPasswordToServer() {
        guard let peripheral = connectedPeripheral,
              let characteristic = writeCharacteristic else { return }
        
        let command = "SET_PASSWORD:\(password)\n"
        if let data = command.data(using: .utf8) {
            isSendingData = true
            peripheral.writeValue(data, for: characteristic, type: .withResponse)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.isSendingData = false
                self.setupStep = .settingSudoPassword
            }
        }
    }
    
    func sendSudoPasswordToServer() {
        guard let peripheral = connectedPeripheral,
              let characteristic = writeCharacteristic else { return }
        
        let command = "SET_SUDO_PASSWORD:\(sudoPassword)\n"
        if let data = command.data(using: .utf8) {
            isSendingData = true
            peripheral.writeValue(data, for: characteristic, type: .withResponse)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                self.isSendingData = false
                self.setupStep = .completed
            }
        }
    }
    
    func completeSetup() {
        guard let peripheral = connectedPeripheral,
              let characteristic = writeCharacteristic else { return }
        
        let command = "COMPLETE:\n"
        if let data = command.data(using: .utf8) {
            peripheral.writeValue(data, for: characteristic, type: .withResponse)
        }
    }
    
    func requestDrives(completion: @escaping ([DirectoryItem]) -> Void) {
        guard let peripheral = connectedPeripheral,
              let characteristic = writeCharacteristic else {
            completion([])
            return
        }
        
        let command = "GET_DRIVES:\n"
        if let data = command.data(using: .utf8) {
            peripheral.writeValue(data, for: characteristic, type: .withResponse)
        }
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            completion([
                DirectoryItem(name: "Root", path: "/"),
                DirectoryItem(name: "Home", path: NSHomeDirectory())
            ])
        }
    }
    
    func requestDirectories(at path: String, completion: @escaping ([DirectoryItem]) -> Void) {
        completion([])
    }
    
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        bluetoothState = central.state
        if central.state == .poweredOn {
            startScanning()
        }
    }
    
    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral, advertisementData: [String : Any], rssi RSSI: NSNumber) {
        if !discoveredServers.contains(where: { $0.identifier == peripheral.identifier }) {
            discoveredServers.append(peripheral)
        }
    }
    
    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        isConnecting = false
        connectedPeripheral = peripheral
        stopScanning()
        peripheral.discoverServices([serviceUUID])
    }
    
    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        isConnecting = false
        connectingPeripheral = nil
    }
    
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let services = peripheral.services else { return }
        
        for service in services {
            if service.uuid == serviceUUID {
                peripheral.discoverCharacteristics([characteristicUUID], for: service)
            }
        }
    }
    
    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard let characteristics = service.characteristics else { return }
        
        for characteristic in characteristics {
            if characteristic.uuid == characteristicUUID {
                writeCharacteristic = characteristic
            }
        }
    }
}

#Preview {
    BluetoothSetupView()
}
