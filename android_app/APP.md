# Android Shareify App

## Status: Under Development

The Android version of the Shareify application is currently under development, based on the iOS app architecture.

## Features

The Android app provides the same core functionality as the iOS version:

- **Cloud and Local Server Connection**: Connect to your Shareify server locally or through the cloud bridge
- **JWT Authentication**: Secure token-based authentication with automatic refresh
- **File Management**: Upload, download, preview, and organize files
- **Customizable Backgrounds**: 19 different background images to personalize your experience
- **Secure Storage**: Uses Android Keystore for secure credential storage
- **Material Design**: Modern Android UI following Material Design 3 guidelines
- **Dark/Light Mode**: Automatic theme switching based on system preferences

## Key Features Planned

- Seamless file sharing experience
- User-friendly interface optimized for Android
- Integration with Shareify ecosystem
- Background customization with high-res images
- Offline support (future enhancement)

## Requirements

- Android 8.0+ (API level 26+)
- A Shareify server running somewhere
- Optional cloud account for remote access

## Building from Source

```bash
git clone https://github.com/bbarni2020/Shareify.git
cd android_app/shareify
./gradlew assembleDebug
```

You can then install the generated APK on your Android device.

## Stay Updated

For updates on the development progress and release dates, please check our main repository or follow our announcement channels.

Thank you for your interest in Shareify for Android!