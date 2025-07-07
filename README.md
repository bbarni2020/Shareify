# Shareify
[![image](https://github.com/user-attachments/assets/3a5cb2ce-0aa7-4490-9f04-dbe67f184279)](https://neighborhood.hackclub.com/) 
![Hackatime Badge](https://hackatime-badge.hackclub.com/U07H3E1CW7J/Shareify)

**When sharing is storing.**

> Transform any device into a powerful personal cloud storage solution with secure file sharing, multi-platform access, and enterprise-grade features.

[![Latest Release](https://img.shields.io/github/v/release/bbarni2020/Shareify)](https://github.com/bbarni2020/Shareify/releases)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://python.org)
[![License](https://img.shields.io/github/license/bbarni2020/Shareify)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/bbarni2020/Shareify)](https://github.com/bbarni2020/Shareify/stargazers)

**Current Version:** 1.0.0 (First Stable Release! 🎉)

## 🌟 What is Shareify?

Shareify is a comprehensive, self-hosted file sharing and Network Attached Storage (NAS) solution that puts you in complete control of your data. Built with modern technologies and designed for both home users and developers, Shareify offers enterprise-grade features with the simplicity of consumer software.

### 🎯 Perfect For
- **Home Users**: Share family photos, documents, and media across all devices
- **Developers**: Open source with well-documented APIs and extensible architecture  
- **Content Creators**: Efficient handling of large files with media previews and collaboration features
- **Small Businesses**: Secure file sharing with user management and access controls

## ✨ Key Features

### 🖥️ **Core Platform**
- **Web-Based Interface**: Beautiful, responsive file management interface
- **Multi-Platform Support**: Windows, macOS, Linux compatibility
- **RESTful API**: Complete API for custom integrations and automation
- **Real-Time Monitoring**: Live system resource tracking and activity logs

### 🔐 **Security & Authentication**
- **JWT Authentication**: Secure token-based authentication system
- **Role-Based Access Control**: Granular permissions and user management
- **FTP Server Integration**: Built-in secure FTP with management tools
- **Activity Tracking**: Comprehensive logging and audit trails

### 📱 **Multi-Platform Access**
- **Native iOS App**: SwiftUI-based mobile interface (v1.0.0)
- **Web Interface**: Full-featured browser-based access
- **API Access**: REST API for custom applications
- **Cloud Integration**: Connect multiple servers through cloud bridge

### ☁️ **Cloud Services**
- **Multi-Server Management**: Manage multiple Shareify instances
- **WebSocket Communication**: Real-time server communication
- **Cloud Bridge**: Secure tunneling for remote access
- **Server Monitoring**: Centralized monitoring and management

### 📁 **File Management**
- **Advanced Operations**: Batch operations, previews, and syntax highlighting
- **Media Support**: Built-in preview for images, videos, and documents
- **Upload/Download**: Drag-and-drop uploads with progress tracking
- **File Organization**: Folder management with search capabilities

## 🏗️ Project Structure

```
Shareify/
├── 📁 host/           # Main server application
│   ├── main.py        # Core Flask application
│   ├── cloud_connection.py  # Cloud bridge client
│   ├── database.py    # Database management
│   └── web/          # Web interface assets
│
├── 📁 cloud/          # Cloud bridge services
│   ├── server.py      # Cloud server implementation
│   ├── main.py        # Command execution API
│   └── templates/     # Web dashboard templates
│
├── 📁 ios_app/        # Native iOS application
│   └── shareify/      # Xcode project
│       ├── ContentView.swift
│       ├── ServerManager.swift
│       └── Settings.swift
│
├── 📁 guides/         # Documentation
│   ├── Install.md     # Installation guide
│   ├── API.md         # API documentation
│   └── ios_app.md     # iOS app guide
│
└── 📁 info/           # Version and release info
    ├── version        # Current version
    └── msg.json       # Release announcements
```

## 🚀 Quick Start

### System Requirements
- **OS**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
- **Python**: 3.7+ (3.9+ recommended)
- **RAM**: 512MB minimum (2GB+ recommended)
- **Storage**: 100MB + space for shared files
- **Network**: Internet connection for setup and cloud features

### Installation

📖 **Check detailed installation guide:** [guides/Install.md](guides/Install.md)

## 📱 iOS App

The native iOS app provides a seamless mobile experience with:

- **Dual Authentication**: Cloud and local server support
- **SwiftUI Interface**: Modern, responsive design
- **Custom Backgrounds**: 19 beautiful background options
- **Secure Storage**: iOS Keychain integration
- **Real-Time Sync**: Live server status monitoring

**Status**: Available (v1.0.0) - Build from source or download from App Store (coming soon)

📖 **iOS app guide:** [guides/ios_app.md](guides/ios_app.md)

## 🔌 API & Integration

Shareify provides a comprehensive REST API for automation and custom integrations.

📖 **Check API documentation:** [guides/API.md](guides/API.md)

## ☁️ Cloud Features

Connect multiple Shareify servers through the cloud bridge:

- **Remote Management**: Control servers from anywhere
- **Multi-Server Dashboard**: Centralized monitoring
- **Secure Tunneling**: Encrypted server communication
- **Command Execution**: Remote server administration

Cloud services are hosted at:
- **Bridge**: `https://bridge.bbarni.hackclub.app`
- **Commands**: `https://command.bbarni.hackclub.app`

## 🛠️ Development

### Building from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bbarni2020/Shareify.git
   cd Shareify
   ```

2. **Install dependencies:**
   ```bash
   cd host
   pip install -r requirements.txt
   ```

3. **Run in development mode:**
   ```bash
   python3 main.py
   ```

### iOS App Development

1. **Open Xcode project:**
   ```bash
   open ios_app/shareify/shareify.xcodeproj
   ```

2. **Configure your development team**
3. **Build and run** (⌘+R)

### Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📊 What's New in v1.0.0

🎉 **First Stable Release!** The complete personal cloud storage solution is here:

- **📱 Native iOS App** - Beautiful SwiftUI interface with real-time monitoring
- **☁️ Cloud Services** - Multi-server management with WebSocket communication  
- **🔐 Enhanced Security** - JWT authentication & role-based access control
- **📁 Advanced File Management** - Batch operations, previews & syntax highlighting
- **👥 Complete User System** - Granular permissions & activity tracking
- **📊 System Monitoring** - Live resource tracking & enhanced logging
- **🔧 FTP Server Integration** - Built-in FTP with full management tools

## 🤝 Community & Support

- **📖 Documentation**: [Comprehensive guides](guides/)
- **🐛 Issue Tracker**: [GitHub Issues](https://github.com/bbarni2020/Shareify/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/bbarni2020/Shareify/discussions)
- **⭐ Star**: Show your support by starring the repository!

## 📄 License

© 2025 Balogh Barnabás. All rights reserved.

Open source file sharing solution - see [LICENSE](LICENSE) for details.

---

<div align="center">

**[Download Shareify](https://github.com/bbarni2020/Shareify/releases) • [Documentation](guides/) • [iOS App Guide](guides/ios_app.md) • [API Reference](guides/API.md)**

</div>