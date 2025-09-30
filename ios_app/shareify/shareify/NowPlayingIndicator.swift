import SwiftUI
import AVKit

struct NowPlayingIndicator: View {
    @StateObject private var playbackManager = PlaybackManager.shared
    @State private var isExpanded = false
    
    var body: some View {
        if let currentMedia = playbackManager.currentlyPlaying {
            VStack(spacing: 0) {
                if isExpanded {
                    expandedView(media: currentMedia)
                } else {
                    compactView(media: currentMedia)
                }
            }
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: isExpanded ? 16 : 12))
            .colorScheme(.light)
            .shadow(color: .black.opacity(0.08), radius: 6, x: 0, y: 3)
            .animation(.spring(response: 0.5, dampingFraction: 0.8), value: isExpanded)
            .onTapGesture {
                withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
                    isExpanded.toggle()
                }
            }
        }
    }
    
    private func compactView(media: MediaItem) -> some View {
        HStack(spacing: 12) {
            albumArt(for: media, size: 45)
            
            VStack(alignment: .leading, spacing: 2) {
                Text(media.name)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                    .lineLimit(1)
                
                Text(media.type == .audio ? "Audio" : "Video")
                    .font(.system(size: 12))
                    .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
            }
            
            Spacer()
            
            playPauseButton(for: media, size: 32)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
    }
    
    private func expandedView(media: MediaItem) -> some View {
        VStack(spacing: 16) {
            HStack {
                albumArt(for: media, size: 60)
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(media.name)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(Color(red: 0x11/255, green: 0x18/255, blue: 0x27/255))
                        .lineLimit(2)
                    
                    Text(media.type == .audio ? "Audio File" : "Video File")
                        .font(.system(size: 13))
                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                }
                
                Spacer()
                
                Button(action: {
                    withAnimation(.spring(response: 0.5, dampingFraction: 0.8)) {
                        isExpanded = false
                    }
                }) {
                    Image(systemName: "chevron.down")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255))
                }
            }
            
            progressBar(for: media)
            
            HStack(spacing: 30) {
                Button(action: { seekBackward(media: media) }) {
                    Image(systemName: "gobackward.15")
                        .font(.system(size: 20))
                        .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                }
                
                playPauseButton(for: media, size: 50)
                
                Button(action: { seekForward(media: media) }) {
                    Image(systemName: "goforward.15")
                        .font(.system(size: 20))
                        .foregroundColor(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }
    
    private func albumArt(for media: MediaItem, size: CGFloat) -> some View {
        RoundedRectangle(cornerRadius: 8)
            .fill(
                LinearGradient(
                    colors: media.type == .audio ? [
                        Color(red: 0x6B/255, green: 0x73/255, blue: 0xFF/255),
                        Color(red: 0x9B/255, green: 0x59/255, blue: 0xB6/255)
                    ] : [
                        Color(red: 0xFF/255, green: 0x6B/255, blue: 0x6B/255),
                        Color(red: 0x4E/255, green: 0xC5/255, blue: 0xFF/255)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .frame(width: size, height: size)
            .overlay(
                Image(systemName: media.type == .audio ? "music.note" : "video.fill")
                    .font(.system(size: size * 0.4))
                    .foregroundColor(.white)
            )
    }
    
    private func playPauseButton(for media: MediaItem, size: CGFloat) -> some View {
        Button(action: { togglePlayPause(media: media) }) {
            Circle()
                .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                .frame(width: size, height: size)
                .overlay(
                    Image(systemName: media.isPlaying ? "pause.fill" : "play.fill")
                        .font(.system(size: size * 0.4))
                        .foregroundColor(.white)
                        .offset(x: media.isPlaying ? 0 : size * 0.04)
                )
                .shadow(color: Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255).opacity(0.2), radius: 3, x: 0, y: 2)
        }
    }
    
    @ViewBuilder
    private func progressBar(for media: MediaItem) -> some View {
        GeometryReader { geometry in
            ZStack(alignment: .leading) {
                RoundedRectangle(cornerRadius: 2)
                    .fill(Color(red: 0x37/255, green: 0x4B/255, blue: 0x63/255).opacity(0.2))
                    .frame(height: 4)
                
                RoundedRectangle(cornerRadius: 2)
                    .fill(Color(red: 0x1E/255, green: 0x29/255, blue: 0x3B/255))
                    .frame(width: geometry.size.width * progressPercentage(for: media), height: 4)
                    .animation(.linear(duration: 0.1), value: progressPercentage(for: media))
            }
        }
        .frame(height: 4)
    }
    
    private func progressPercentage(for media: MediaItem) -> CGFloat {
        guard let currentItem = media.player.currentItem,
              currentItem.duration.isValid,
              !currentItem.duration.seconds.isNaN,
              currentItem.duration.seconds > 0 else {
            return 0
        }
        
        let current = media.player.currentTime().seconds
        let total = currentItem.duration.seconds
        
        return CGFloat(current / total)
    }
    
    private func togglePlayPause(media: MediaItem) {
        if media.isPlaying {
            media.player.pause()
        } else {
            media.player.play()
        }
        media.isPlaying.toggle()
    }
    
    private func seekForward(media: MediaItem) {
        let currentTime = media.player.currentTime().seconds
        let newTime = currentTime + 15
        media.player.seek(to: CMTime(seconds: newTime, preferredTimescale: 600))
    }
    
    private func seekBackward(media: MediaItem) {
        let currentTime = media.player.currentTime().seconds
        let newTime = max(currentTime - 15, 0)
        media.player.seek(to: CMTime(seconds: newTime, preferredTimescale: 600))
    }
}