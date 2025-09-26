# Shareify Android App

I wanted to access my NAS from my Android phone without using some sketchy third-party app, so I built this. It's a native Android app that connects to your Shareify server (and the cloud service if you're using that too).

Built with Jetpack Compose because it's the modern way to build Android UIs and provides great compatibility with Material Design 3.

## What it does

**Connects to both things:**
- Your local Shareify server (the one you installed)
- The cloud service (if you want that too)
- Uses JWT tokens because that's what everything uses these days

**Actually feels like an Android app:**
- Built with Jetpack Compose following Material Design 3 patterns
- Has 19 background options (matching the iOS version)
- Smooth animations that look natural on Android
- Follows Android design principles and guidelines

**Manages your accounts:**
- Change passwords without going to the web interface
- View your profile stuff
- Everything stored securely with Android Keystore encryption

**Customizable enough:**
- Pick different backgrounds (1-19)
- Settings actually stick between launches
- Dark/light mode support (follows system theme)

## Getting Started

**You'll need:**
- Android 8.0+ (API level 26+) - covers 95%+ of active devices
- A Shareify server running somewhere
- Maybe a cloud account if you're into that

**Installation:**
- APK releases coming soon™
- Or build it yourself if you have Android Studio

**First time setup:**
1. App walks you through the basic setup
2. Log into your cloud account and/or local server
3. Start using it

## How it's built

**Main screens:**

**Onboarding** - Quick intro to Shareify with feature highlights and setup guidance.

**Login** - Standard email/password form for cloud accounts. Handles tokens automatically so you don't have to think about it.

**Server Login** - Connect to your local server. You can put in custom URLs, ports, whatever. It'll test the connection before saving.

**Home** - Shows your files and recent stuff. Nothing fancy, just gets you where you need to go.

**Settings** - Change passwords, pick backgrounds, logout, the usual settings stuff.

**The code structure:**

I split things into proper Android architecture patterns:

`Repository` - Handles talking to servers, API calls, auth tokens, error handling, and data caching

`ViewModels` - Manage UI state and business logic using MVVM pattern

`Compose UI` - Modern declarative UI built with Jetpack Compose and Material Design 3

`Secure Storage` - Uses Android Keystore and EncryptedSharedPreferences for sensitive data

## Cloud integration

The flow is pretty straightforward:
1. You log in with email/password
2. App gets a JWT token from the cloud service  
3. Uses that token to talk to your local servers through the command API
4. Handles token refresh in the background

Works with custom endpoints too if you're running your own cloud instance.

## Security stuff

- Everything sensitive goes in Android Keystore (encrypted at hardware level when available)
- JWT tokens are encrypted when stored
- All network requests use HTTPS/TLS
- Auto-logout when sessions expire
- Doesn't track anything or send analytics anywhere
- Follows Android security best practices

## Customization

The 19 background images thing matches the iOS version. They're references to drawable resources and handle different screen sizes and densities properly.

**Building from source:**
```bash
git clone https://github.com/bbarni2020/Shareify.git
cd android_app/shareify
./gradlew assembleDebug
```

You'll need Android Studio or at least the Android SDK, then run the build. The APK will be generated in `app/build/outputs/apk/debug/`.

## When things break

**Connection issues:**
- Double-check your server URL and port
- Make sure your network actually works
- Check if your server's firewall is blocking the app
- SSL certificate problems are usually the server's fault

**Login problems:**
- App should handle token refresh automatically, but sometimes it doesn't
- Try logging out and back in
- Make sure your account actually works (test on the web interface)
- Server version might be too old/new

**Performance:**
- Check Android background app restrictions in Settings
- Make sure you have storage space
- Update Android if you're on something ancient
- Clear app data if things get really weird

If none of that works, check the GitHub issues or file a new one.

## Development Setup

**Prerequisites:**
- Android Studio Arctic Fox or newer
- Android SDK 26+ (Android 8.0+)
- Kotlin 1.9.20+
- Gradle 8.4+

**Dependencies:**
- Jetpack Compose for UI
- Retrofit for networking
- Material Design 3 components
- Android Keystore for security
- JWT libraries for token handling

**Architecture:**
- MVVM pattern with ViewModels
- Repository pattern for data layer
- Compose for declarative UI
- Coroutines for async operations

## Current status

**Version**: 1.0.0  
**Android**: 8.0+ (API 26+)  
**Last updated**: January 2025  
**Status**: Works on my Pixel

## Notes

This is the Android equivalent of the iOS app, so feature parity should be pretty close. I use Material Design 3 instead of trying to copy iOS patterns because that would look weird on Android.

The Play Store version might take a while because Google's review process is... Google's review process. You can build from source in the meantime.

Planning to add offline support and better file management, but that's future me's problem.

## API Compatibility

The Android app uses the same API endpoints as the iOS version:
- `https://bridge.bbarni.hackclub.app` for cloud authentication
- `https://command.bbarni.hackclub.app` for server communication
- Standard REST endpoints for file operations

This means any server that works with the iOS app will work with Android too.

---

For the server stuff, check the main Shareify docs. This is just about the Android app.