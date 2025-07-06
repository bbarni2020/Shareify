# Shareify iOS App

The Shareify iOS app provides a native mobile interface for accessing your Shareify server and cloud services. Built with SwiftUI, it offers a seamless and intuitive experience for managing your files on the go.

## Features

### 🌐 Dual Authentication System
- **Cloud Account**: Connect to Shareify's cloud services
- **Local Server**: Direct connection to your self-hosted Shareify server
- Secure JWT-based authentication for both services

### 📱 Native iOS Experience
- **SwiftUI Interface**: Modern, responsive design that follows iOS design guidelines
- **Custom Backgrounds**: Choose from 19 beautiful background images
- **Smooth Animations**: Fluid transitions and interactions
- **Haptic Feedback**: Tactile feedback for enhanced user experience

### 🔐 Account Management
- **Password Reset**: Change passwords for both cloud and local accounts
- **Profile Information**: View and manage your account details
- **Secure Storage**: All credentials stored securely in iOS Keychain

### 🎨 Customization
- **Background Selection**: Personalize your app with custom backgrounds
- **Dynamic Theming**: Adaptive UI that responds to your choices
- **Settings Persistence**: Your preferences are saved across app launches

## Getting Started

### Requirements
- iOS 15.0 or later
- Active Shareify cloud account
- Self-hosted Shareify server

### Installation
1. Download the app from the App Store (coming soon)
2. Or build from source using Xcode

### First Launch
1. **Onboarding**: The app guides you through initial setup
2. **Account Setup**: Log in to cloud and your local server
3. **Use the app**: You are ready to go!

## App Structure

### Main Views

#### 📱 **Login Screen**
- Cloud account authentication
- Email and password input
- Automatic token management
- Error handling and validation

#### 🖥️ **Server Login**
- Local server connection
- Custom server URL input
- Port and protocol configuration
- Connection testing

#### 🏠 **Home Dashboard**
- Quick access to files and folders
- Recent activity overview
- Server status indicators
- Navigation to other sections

#### ⚙️ **Settings**
- Account management
- Background customization
- Security settings
- App information

#### 🔑 **Password Reset**
- Secure password change flow
- Separate flows for cloud and local accounts
- Email verification (cloud accounts)
- Instant validation feedback

### Key Components

#### 🎯 **ServerManager**
```swift
// Handles all server communications
- API endpoint management
- Request authentication
- Response processing
- Error handling
```

#### 🖼️ **BackgroundManager**
```swift
// Manages app theming and backgrounds
- Background selection persistence
- Dynamic image loading
- Theme coordination
- User preference storage
```

#### 🔐 **Authentication System**
```swift
// Secure credential management
- JWT token handling
- Keychain integration
- Session management
- Auto-refresh capabilities
```

## Cloud Integration

### Authentication Flow
1. **Login**: User enters email and password
2. **Token Exchange**: App receives JWT token from cloud service
3. **Server Registration**: Token used to authenticate with local servers
4. **Session Management**: Automatic token refresh and validation

### Features
- Direct file access
- Real-time synchronization
- Offline capability planning
- Custom endpoint support

## Security Features

### Data Protection
- **Keychain Storage**: All sensitive data stored in iOS Keychain
- **Token Encryption**: JWT tokens encrypted at rest
- **Secure Communication**: HTTPS/TLS for all network requests
- **Auto-logout**: Automatic session expiration handling

### Privacy
- **Local Storage**: Minimal data stored locally
- **No Tracking**: No user behavior tracking
- **Secure Defaults**: Security-first configuration

## Customization

### Background Images
The app includes 19 beautiful background images:
- High-resolution images optimized for iOS devices
- Automatic aspect ratio handling
- Smooth transition animations

### Building from Source
1. **Clone Repository**: `git clone https://github.com/bbarni2020/Shareify.git`
2. **Open Xcode**: Navigate to `ios_app/shareify/shareify.xcodeproj`
3. **Configure Team**: Set your developer team in project settings
4. **Build**: Command+R to build and run

## Troubleshooting

### Common Issues

#### Connection Problems
- **Check Server URL**: Ensure correct server address and port
- **Network Access**: Verify internet connectivity
- **Firewall Settings**: Check if server ports are accessible
- **SSL Certificates**: Ensure valid HTTPS certificates

#### Authentication Issues
- **Token Expiry**: App automatically handles token refresh
- **Invalid Credentials**: Double-check email and password
- **Server Compatibility**: Ensure server version compatibility
- **Account Status**: Verify account is active and accessible

#### App Performance
- **Background Refresh**: Check iOS background app refresh settings
- **Storage Space**: Ensure sufficient device storage
- **iOS Version**: Update to latest supported iOS version
- **App Updates**: Keep app updated to latest version

### Getting Help
- **Documentation**: Check the full Shareify documentation
- **GitHub Issues**: Report bugs on the GitHub repository
- **Community**: Join the Shareify community discussions

## Version Information

**Current Version**: 1.0.0  
**iOS Compatibility**: iOS 15.0+  
**Last Updated**: July 2025  
**Developer**: Balogh Barnabás

## License

© 2025 Balogh Barnabás. All rights reserved.

---

*This documentation covers the Shareify iOS app. For server installation and API documentation, please refer to the main Shareify documentation.*