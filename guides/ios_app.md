# Shareify iOS App

I wanted to access my NAS from my phone without using some sketchy third-party app, so I built this. It's a native iOS app that connects to your Shareify server (and the cloud service if you're using that too).

Built with SwiftUI because, honestly, UIKit is getting old and Apple keeps pushing SwiftUI anyway.

## What it does

**Connects to both things:**
- Your local Shareify server (the one you installed)
- The cloud service (if you want that too)
- Uses JWT tokens because that's what everything uses these days

**Actually feels like an iOS app:**
- Built with SwiftUI so it follows iOS design patterns
- Has 19 background images (I got a bit carried away with the design)
- Haptic feedback because why not
- Smooth animations that don't make you want to throw your phone

**Manages your accounts:**
- Change passwords without going to the web interface
- View your profile stuff
- Everything stored in iOS Keychain (much more secure than just saving to UserDefaults)

**Customizable enough:**
- Pick different backgrounds
- Settings actually stick between launches
- Dark/light mode support

## Getting Started

**You'll need:**
- iOS 15.0+ (older versions weren't worth supporting)
- A Shareify server running somewhere
- Maybe a cloud account if you're into that

**Installation:**
- App Store version is coming soon™
- Or build it yourself if you have Xcode

**First time setup:**
1. App walks you through the basic setup
2. Log into your cloud account and/or local server
3. Start using it

## How it's built

**Main screens:**

**Login** - Pretty standard email/password form for cloud accounts. Handles tokens automatically so you don't have to think about it.

**Server Login** - Connect to your local server. You can put in custom URLs, ports, whatever. It'll test the connection before saving.

**Home** - Shows your files and recent stuff. Nothing fancy, just gets you where you need to go.

**Settings** - Change passwords, pick backgrounds, the usual settings stuff.

**Password Reset** - Separate flows for cloud vs local accounts because they work differently.

**The code structure:**

I split things into managers because everything in one file is a nightmare:

`ServerManager` - Handles talking to servers, API calls, auth tokens, error handling

`BackgroundManager` - Manages the background images and themes. Saves your preferences.

`Authentication System` - JWT tokens, Keychain storage, session stuff. Tries to refresh tokens automatically.

## Cloud integration

The flow is pretty straightforward:
1. You log in with email/password
2. App gets a JWT token from the cloud service  
3. Uses that token to talk to your local servers
4. Handles token refresh in the background

Works with custom endpoints too if you're running your own cloud instance.

## Security stuff

- Everything sensitive goes in iOS Keychain (not just UserDefaults like some apps)
- JWT tokens are encrypted when stored
- All network requests use HTTPS/TLS
- Auto-logout when sessions expire
- Doesn't track anything or send analytics anywhere

## Customization

The 19 background images thing started as "I'll add a few options" and got out of hand. They're high-res and handle different screen sizes properly.

**Building from source:**
```bash
git clone https://github.com/bbarni2020/Shareify.git
cd ios_app/shareify
open shareify.xcodeproj
```

You'll need to set your developer team in Xcode, then hit Command+R to build.

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
- Check iOS background app refresh settings
- Make sure you have storage space
- Update iOS if you're on something ancient
- Update the app when I release fixes

If none of that works, check the GitHub issues or file a new one.

## Current status

**Version**: 1.0.0  
**iOS**: 15.0+  
**Last updated**: July 2025  
**Status**: Works on my phone

## Notes

This is still pretty new, so there might be bugs. I use it daily on my iPhone 16e, but different devices/iOS versions might have issues.

The App Store version is taking forever because Apple's review process is... Apple's review process. You can build from source in the meantime.

Planning to add offline support and better file management, but that's future me's problem.

---

For the server stuff, check the main Shareify docs. This is just about the iOS app.