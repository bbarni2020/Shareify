import SwiftUI
import AVKit
import AVFoundation
import Combine
import MediaPlayer
import UIKit

struct MediaPlayerView: View {
    let file: FinderItem
    let content: String
    let onDismiss: () -> Void
    @StateObject private var playbackManager = PlaybackManager.shared
    
    var body: some View {
        if content.isEmpty {
            LoadingMediaView(file: file, onDismiss: onDismiss)
        } else if PreviewHelper.isVideoFile(file.name.lowercased()) {
            CustomVideoPlayerView(file: file, content: content, onDismiss: onDismiss)
        } else if PreviewHelper.isAudioFile(file.name.lowercased()) {
            CustomAudioPlayerView(file: file, content: content, onDismiss: onDismiss)
        }
    }
}

struct CustomVideoPlayerView: View {
    let file: FinderItem
    let content: String
    let onDismiss: () -> Void
    
    @State private var player: AVPlayer?
    @State private var isPlaying = false
    @State private var currentTime: Double = 0
    @State private var duration: Double = 0
    @State private var showControls = true
    @State private var controlsTimer: Timer?
    @State private var cancellables = Set<AnyCancellable>()
    @StateObject private var playbackManager = PlaybackManager.shared
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                backgroundView(geometry: geometry)
                
                VStack(spacing: 0) {
                    topControlBar
                    
                    ZStack {
                        videoPlayerView
                        
                        if showControls {
                            overlayControls
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
                    .colorScheme(.light)
                    .padding(.horizontal, 20)
                    .padding(.bottom, 20)
                }
            }
        }
        .onAppear {
            setupPlayer()
            startControlsTimer()
        }
        .onDisappear {
            cleanup()
        }
    }
    
    @ViewBuilder
    private func backgroundView(geometry: GeometryProxy) -> some View {
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
            )
    }
    
    private var topControlBar: some View {
        HStack {
            Button(action: onDismiss) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            Spacer()
            
            Text("Video Player")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            
            Spacer()
            
            Button(action: {}) {
                Image(systemName: "ellipsis")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 60)
        .padding(.bottom, 15)
    }
    
    @ViewBuilder
    private var videoPlayerView: some View {
        if let player = player {
            VideoPlayer(player: player)
                .cornerRadius(12)
                .onTapGesture {
                    toggleControlsVisibility()
                }
                .onAppear {
                    playbackManager.currentlyPlaying = MediaItem(
                        name: file.name,
                        type: .video,
                        player: player
                    )
                }
        }
    }
    
    @ViewBuilder
    private var overlayControls: some View {
        VStack {
            Spacer()
            
            VStack(spacing: 20) {
                Text(file.name)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.white)
                    .lineLimit(1)
                    .padding(.horizontal, 20)
                
                progressSlider
                
                HStack(spacing: 40) {
                    Button(action: seekBackward) {
                        Image(systemName: "gobackward.15")
                            .font(.system(size: 24))
                            .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                    }
                    
                    Button(action: togglePlayPause) {
                        Circle()
                            .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                            .frame(width: 60, height: 60)
                            .overlay(
                                Image(systemName: isPlaying ? "pause.fill" : "play.fill")
                                    .font(.system(size: 24))
                                    .foregroundColor(.white)
                                    .offset(x: isPlaying ? 0 : 2)
                            )
                            .shadow(color: .black.opacity(0.2), radius: 4, x: 0, y: 2)
                    }
                    
                    Button(action: seekForward) {
                        Image(systemName: "goforward.15")
                            .font(.system(size: 24))
                            .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                    }
                }
                
                HStack {
                    Text(formatTime(currentTime))
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundColor(.white)
                    
                    Spacer()
                    
                    Text(formatTime(duration))
                        .font(.system(size: 12, design: .monospaced))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 20)
            }
            .padding(.vertical, 20)
            .background(
                LinearGradient(
                    colors: [Color.clear, Color.black.opacity(0.7)],
                    startPoint: .top,
                    endPoint: .bottom
                )
            )
        }
        .transition(.opacity)
    }
    
    private var progressSlider: some View {
        VStack(spacing: 8) {
            Slider(value: $currentTime, in: 0...max(duration, 1)) { editing in
                if !editing {
                    player?.seek(to: CMTime(seconds: currentTime, preferredTimescale: 600))
                }
            }
            .accentColor(.white)
            .padding(.horizontal, 20)
        }
    }
    
    private func setupPlayer() {
        guard let videoData = Data(base64Encoded: content) else { return }
        
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
        do {
            try videoData.write(to: tempURL)
            player = AVPlayer(url: tempURL)
            
            player?.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.5, preferredTimescale: 600), queue: .main) { time in
                currentTime = time.seconds
            }
            
            NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { _ in
                isPlaying = false
                currentTime = 0
                player?.seek(to: .zero)
            }
            
            player?.currentItem?.publisher(for: \.duration)
                .compactMap { $0.seconds }
                .filter { !$0.isNaN }
                .receive(on: DispatchQueue.main)
                .sink { duration in
                    self.duration = duration
                }
                .store(in: &cancellables)
        } catch {
            print("Failed to setup video player: \(error)")
        }
    }
    
    private func togglePlayPause() {
        guard let player = player else { return }
        
        if isPlaying {
            player.pause()
        } else {
            player.play()
        }
        isPlaying.toggle()
        
        if let currentMedia = playbackManager.currentlyPlaying {
            currentMedia.isPlaying = isPlaying
        }
    }
    
    private func seekForward() {
        let newTime = min(currentTime + 15, duration)
        player?.seek(to: CMTime(seconds: newTime, preferredTimescale: 600))
    }
    
    private func seekBackward() {
        let newTime = max(currentTime - 15, 0)
        player?.seek(to: CMTime(seconds: newTime, preferredTimescale: 600))
    }
    
    private func toggleControlsVisibility() {
        withAnimation(.easeInOut(duration: 0.3)) {
            showControls.toggle()
        }
        
        if showControls {
            startControlsTimer()
        }
    }
    
    private func startControlsTimer() {
        controlsTimer?.invalidate()
        controlsTimer = Timer.scheduledTimer(withTimeInterval: 3.0, repeats: false) { _ in
            withAnimation(.easeInOut(duration: 0.3)) {
                showControls = false
            }
        }
    }
    
    private func formatTime(_ time: Double) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func cleanup() {
        player?.pause()
        controlsTimer?.invalidate()
        playbackManager.currentlyPlaying = nil
        
        if let player = player, let currentItem = player.currentItem {
            NotificationCenter.default.removeObserver(self, name: .AVPlayerItemDidPlayToEndTime, object: currentItem)
        }
        
        cancellables.removeAll()
    }
}

struct CustomAudioPlayerView: View {
    let file: FinderItem
    let content: String
    let onDismiss: () -> Void
    
    @State private var player: AVPlayer?
    @State private var isPlaying = false
    @State private var currentTime: Double = 0
    @State private var duration: Double = 0
    @State private var cancellables = Set<AnyCancellable>()
    @State private var isPlayerReady = false
    @State private var timeObserver: Any?
    @State private var remoteConfigured = false
    @StateObject private var playbackManager = PlaybackManager.shared
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                backgroundView(geometry: geometry)
                
                VStack(spacing: 0) {
                    topNavigationBar
                    
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
                        .ignoresSafeArea(.all, edges: [.bottom, .leading, .trailing])
                        .overlay(
                            VStack(spacing: 30) {
                                Spacer()
                                
                                albumArtView
                                
                                VStack(spacing: 20) {
                                    Text(file.name)
                                        .font(.system(size: 20, weight: .semibold))
                                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                        .lineLimit(2)
                                        .multilineTextAlignment(.center)
                                    
                                    progressView
                                    
                                    controlsView
                                }
                                .padding(.horizontal, 40)
                                
                                Spacer()
                                Spacer()
                            }
                        )
                }
            }
        }
        .onAppear {
            setupPlayer()
        }
        .onDisappear {
            cleanup()
        }
    }
    
    @ViewBuilder
    private func backgroundView(geometry: GeometryProxy) -> some View {
        Image(backgroundManager.backgroundImageName)
            .resizable()
            .aspectRatio(contentMode: .fill)
            .frame(width: geometry.size.width, height: geometry.size.height)
            .clipped()
            .ignoresSafeArea(.all)
    }
    
    private var topNavigationBar: some View {
        HStack {
            Button(action: onDismiss) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            Spacer()
            
            Text("Now Playing")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            
            Spacer()
            
            Button(action: {}) {
                Image(systemName: "ellipsis")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 60)
        .padding(.bottom, 15)
    }
    
    private var albumArtView: some View {
        RoundedRectangle(cornerRadius: 20)
            .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
            .frame(width: 220, height: 220)
            .overlay(
                Image(systemName: "music.note")
                    .font(.system(size: 64))
                    .foregroundColor(.white.opacity(0.8))
            )
            .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
    }
    
    private var progressView: some View {
        VStack(spacing: 8) {
            Slider(value: $currentTime, in: 0...max(duration, 1)) { editing in
                if !editing {
                    player?.seek(to: CMTime(seconds: currentTime, preferredTimescale: 600))
                }
            }
            .accentColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
            
            HStack {
                Text(formatTime(currentTime))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                
                Spacer()
                
                Text(formatTime(duration))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
            }
        }
    }
    
    private var controlsView: some View {
        HStack(spacing: 50) {
            Button(action: seekBackward) {
                Image(systemName: "gobackward.15")
                    .font(.system(size: 28))
                    .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
            }
            
            Button(action: togglePlayPause) {
                Circle()
                    .fill(isPlayerReady ? Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255) : Color.gray)
                    .frame(width: 70, height: 70)
                    .overlay(
                        Group {
                            if !isPlayerReady {
                                ProgressView()
                                    .scaleEffect(0.8)
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            } else {
                                Image(systemName: isPlaying ? "pause.fill" : "play.fill")
                                    .font(.system(size: 28))
                                    .foregroundColor(.white)
                                    .offset(x: isPlaying ? 0 : 2)
                            }
                        }
                    )
                    .shadow(color: Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255).opacity(0.3), radius: 8, x: 0, y: 4)
            }
            .disabled(!isPlayerReady)
            
            Button(action: seekForward) {
                Image(systemName: "goforward.15")
                    .font(.system(size: 28))
                    .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
            }
        }
    }
    
    private func setupPlayer() {
        guard let audioData = Data(base64Encoded: content) else { 
            print("Failed to decode base64 content")
            print("Content length: \(content.count)")
            print("Content preview: \(String(content.prefix(100)))")
            return 
        }
        
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default, options: [.allowBluetoothHFP, .allowBluetoothA2DP])
            try AVAudioSession.sharedInstance().setActive(true)
            print("Audio session configured successfully")
        } catch {
            print("Failed to configure audio session: \(error)")
        }
        
        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent(file.name)
        do {
            try audioData.write(to: tempURL)
            print("Audio file written to: \(tempURL)")
            print("File size: \(audioData.count) bytes")
            
            player = AVPlayer(url: tempURL)

            player?.automaticallyWaitsToMinimizeStalling = false
            
            playbackManager.currentlyPlaying = MediaItem(
                name: file.name,
                type: .audio,
                player: player!
            )

            configureRemoteCommands()
            
            timeObserver = player?.addPeriodicTimeObserver(forInterval: CMTime(seconds: 0.5, preferredTimescale: 600), queue: .main) { time in
                currentTime = time.seconds
                updateNowPlayingInfo()
            }
            
            NotificationCenter.default.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: player?.currentItem, queue: .main) { _ in
                isPlaying = false
                currentTime = 0
                player?.seek(to: .zero)
                playbackManager.currentlyPlaying?.isPlaying = false
            }
            
            player?.currentItem?.publisher(for: \.duration)
                .compactMap { $0.seconds }
                .filter { !$0.isNaN }
                .receive(on: DispatchQueue.main)
                .sink { duration in
                    self.duration = duration
                }
                .store(in: &cancellables)

            player?.currentItem?.publisher(for: \.status)
                .receive(on: DispatchQueue.main)
                .sink { status in
                    switch status {
                    case .readyToPlay:
                        print("Audio player ready to play")
                        self.isPlayerReady = true
                        self.updateNowPlayingInfo()
                    case .failed:
                        if let error = self.player?.currentItem?.error {
                            print("Audio player failed: \(error.localizedDescription)")
                        }
                        self.isPlayerReady = false
                    case .unknown:
                        print("Audio player status unknown")
                        self.isPlayerReady = false
                    @unknown default:
                        print("Audio player unknown status")
                        self.isPlayerReady = false
                    }
                }
                .store(in: &cancellables)
        } catch {
            print("Failed to setup audio player: \(error)")
        }
    }
    
    private func togglePlayPause() {
        guard let player = player, isPlayerReady else { 
            print("Player not available or not ready")
            return 
        }
        
        print("Toggle play/pause - current state: \(isPlaying ? "playing" : "paused")")
        print("Player rate: \(player.rate)")
        
        if isPlaying {
            player.pause()
            print("Pausing player")
        } else {
            player.play()
            print("Starting player")
        }
        isPlaying.toggle()
        updateNowPlayingInfo()
        
        if let currentMedia = playbackManager.currentlyPlaying {
            currentMedia.isPlaying = isPlaying
        }
    }
    
    private func seekForward() {
        let newTime = min(currentTime + 15, duration)
        player?.seek(to: CMTime(seconds: newTime, preferredTimescale: 600))
    }
    
    private func seekBackward() {
        let newTime = max(currentTime - 15, 0)
        player?.seek(to: CMTime(seconds: newTime, preferredTimescale: 600))
    }
    
    private func formatTime(_ time: Double) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func cleanup() {
        if let token = timeObserver { player?.removeTimeObserver(token) }
        if let player = player, let currentItem = player.currentItem {
            NotificationCenter.default.removeObserver(self, name: .AVPlayerItemDidPlayToEndTime, object: currentItem)
        }
        cancellables.removeAll()
    }

    private func updateNowPlayingInfo() {
        guard isPlayerReady else { return }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: file.name,
            MPMediaItemPropertyArtist: "",
            MPNowPlayingInfoPropertyElapsedPlaybackTime: currentTime,
            MPMediaItemPropertyPlaybackDuration: duration,
            MPNowPlayingInfoPropertyPlaybackRate: isPlaying ? 1 : 0,
            MPNowPlayingInfoPropertyDefaultPlaybackRate: 1.0
        ]
        if let item = player?.currentItem, let asset = item.asset as? AVURLAsset {
            info[MPMediaItemPropertyAssetURL] = asset.url
        }
        if let img = UIImage(systemName: "music.note")?.withTintColor(.white, renderingMode: .alwaysOriginal) {
            let artwork = MPMediaItemArtwork(boundsSize: img.size) { _ in img }
            info[MPMediaItemPropertyArtwork] = artwork
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    private func configureRemoteCommands() {
        if remoteConfigured { return }
        remoteConfigured = true
        let center = MPRemoteCommandCenter.shared()
        center.playCommand.isEnabled = true
        center.pauseCommand.isEnabled = true
        center.togglePlayPauseCommand.isEnabled = true
        center.playCommand.addTarget { _ in
            if !isPlaying { togglePlayPause() }
            return .success
        }
        center.pauseCommand.addTarget { _ in
            if isPlaying { togglePlayPause() }
            return .success
        }
        center.togglePlayPauseCommand.addTarget { _ in
            togglePlayPause()
            return .success
        }
        center.nextTrackCommand.isEnabled = false
        center.previousTrackCommand.isEnabled = false
    }
}

class PlaybackManager: ObservableObject {
    static let shared = PlaybackManager()
    
    @Published var currentlyPlaying: MediaItem?
    
    private init() {}
}

class MediaItem: ObservableObject {
    let name: String
    let type: MediaType
    let player: AVPlayer
    @Published var isPlaying: Bool = false
    
    enum MediaType {
        case audio, video
    }
    
    init(name: String, type: MediaType, player: AVPlayer) {
        self.name = name
        self.type = type
        self.player = player
    }
}

struct LoadingMediaView: View {
    let file: FinderItem
    let onDismiss: () -> Void
    @StateObject private var backgroundManager = BackgroundManager.shared
    
    var body: some View {
        GeometryReader { geometry in
            ZStack {
                backgroundView(geometry: geometry)
                
                VStack(spacing: 0) {
                    topNavigationBar
                    
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
                        .ignoresSafeArea(.all, edges: [.bottom, .leading, .trailing])
                        .overlay(
                            VStack(spacing: 40) {
                                Spacer()
                                
                                RoundedRectangle(cornerRadius: 20)
                                    .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                                    .frame(width: 220, height: 220)
                                    .overlay(
                                        VStack(spacing: 16) {
                                            ProgressView()
                                                .scaleEffect(2)
                                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                            
                                            Text("Loading...")
                                                .font(.system(size: 16, weight: .medium))
                                                .foregroundColor(.white)
                                        }
                                    )
                                    .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
                                
                                Text(file.name)
                                    .font(.system(size: 20, weight: .semibold))
                                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                                    .lineLimit(2)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 40)
                                
                                Spacer()
                                Spacer()
                            }
                        )
                }
            }
        }
    }
    
    @ViewBuilder
    private func backgroundView(geometry: GeometryProxy) -> some View {
        Image(backgroundManager.backgroundImageName)
            .resizable()
            .aspectRatio(contentMode: .fill)
            .frame(width: geometry.size.width, height: geometry.size.height)
            .clipped()
            .ignoresSafeArea(.all)
    }
    
    private var topNavigationBar: some View {
        HStack {
            Button(action: onDismiss) {
                Image(systemName: "chevron.left")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
            
            Spacer()
            
            Text("Loading Media")
                .font(.system(size: 20, weight: .bold))
                .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            
            Spacer()
            
            Button(action: {}) {
                Image(systemName: "ellipsis")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 60)
        .padding(.bottom, 15)
    }
}
