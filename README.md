# Shareify
[![image](https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/website/Shareify_name_logo.png)](https://bbarni2020.github.io/Shareify) 
![Hackatime Badge](https://hackatime-badge.hackclub.com/U07H3E1CW7J/Shareify)

**When sharing is storing.**

[![Latest Release](https://img.shields.io/github/v/release/bbarni2020/Shareify)](https://github.com/bbarni2020/Shareify/releases)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://python.org)
[![License](https://img.shields.io/github/license/bbarni2020/Shareify)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/bbarni2020/Shareify)](https://github.com/bbarni2020/Shareify/stargazers)

**v1.0.0** - Finally calling this stable after months of daily use 🎉

## Why I built this

Got fed up with paying Dropbox $10/month just to store family photos, then hitting upload limits when trying to share a 2GB video with friends. Plus accessing work files from home was always a pain.

So I built my own thing. It's basically a personal file server that you can reach from anywhere - no subscription fees, no upload limits, no "premium features" locked behind paywalls.

Been running it on my old MacBook for 6 months now. It just sits there serving files while I'm at work, friends can grab stuff I share, and I can access everything from my phone when I'm out.

This works well if you:
- Have an old computer lying around that could be useful
- Want to share big files without email size limits  
- Don't trust putting everything on Google Drive
- Like having control over your own stuff
- Need to access files from multiple devices/locations

## Quick start (the impatient version)

Need Python 3.7+ and about 100MB space. Works on Windows/Mac/Linux.

```bash
git clone https://github.com/bbarni2020/Shareify.git
cd Shareify
pip install -r requirements.txt
python3 main.py
```

Open `http://localhost:6969` and you're running. Default login is admin/admin (change it immediately).

Full setup guide is in [guides/Install.md](guides/Install.md) if you want the details.

### Or just use the prebuilt executables (Windows, macOS & Linux)

If you don't feel like messing with Python or pip, grab the latest release from the **Releases** page. There are standalone executables for Windows (.exe), macOS (app/bundle), and Linux (`shareify` binary).

How it goes:
- Download the archive (zip/tar) for your OS
- Unzip/extract it wherever (Desktop, Downloads, etc)
- On Windows: double‑click `Shareify.exe`
- On macOS: first launch might trigger Gatekeeper — right‑click > Open the first time
- On Linux: run `chmod +x shareify`, then launch it from your terminal or file manager
- A console/terminal window pops up and the server starts right away

Then just hit: http://localhost:6969

Default credentials for the executable builds:
```
user: admin
password: root
```
(Yep, that's different from the source install example above — change it ASAP either way.)

No install steps, no virtualenv, no pip. Just run it. If you ever want to hack on the code, you can always switch to the full source setup later.

## What you actually get

The web interface is drag-and-drop simple. I kept it minimal because I got tired of bloated file managers. You can:

- Upload stuff by dragging files into the browser
- Preview images, videos, text files without downloading
- Create folders, move files around
- Share links that work from outside your network (through the bridge)
- Set up different users with different access levels

The **mobile situation**: Mobile browser experience sucked, so I built a proper iOS app. It's in the ios_app folder if you want to build it yourself. Handles switching between local/remote connections automatically.

**Security bits**: JWT tokens for auth, SQLite for user management, HTTPS if you set it up. There's also an FTP server built in because sometimes you just need FTP.

**The bridge thing**: This took me forever to figure out. Basically lets you access your server from anywhere without dealing with port forwarding or dynamic DNS. Your server connects to my bridge service, and when you access it remotely, requests get relayed back to your machine. The bridge can't see your files - it's just passing encrypted requests through.

Some other stuff that's in there:
- File syntax highlighting (supports like 50+ languages)
- Batch operations for handling multiple files
- System monitoring so you can see if your server's dying
- REST API for automation or building other tools
- Activity logs to see who accessed what
- WebSocket updates so the UI feels snappy

## Project structure

```
Shareify/
├── host/              # Main server (this is what you run)
│   ├── main.py        # Flask app entry point
│   ├── cloud_connection.py  # Bridge communication
│   ├── database.py    # SQLite wrapper
│   └── web/           # Static files (HTML/CSS/JS)
│
├── cloud/             # Bridge services (I host these)
│   ├── server.py      # WebSocket relay server
│   ├── main.py        # Command API server
│   └── templates/     # Web dashboard for bridge
│
├── current/           # Development helpers (installers, launchers, mirrors)
│   ├── main.py
│   ├── launcher.py
│   └── settings/
│
├── static/            # Shared static assets and templates used by cloud/host
│   └── templates/
│
├── ios_app/           # Native iOS app (Xcode project)
│   └── shareify/
│
├── guides/            # Documentation (Install, API, iOS guide...)
│
├── website/           # Marketing / website assets
│
├── info/              # Version info (version file, update messages)
│   ├── version
│   └── msg.json
│
├── som-demo/          # small demo site
│
├── cloud-bridge.html  # misc root-level files
├── index.html
├── README.md
├── package.json
├── style.css
└── LICENSE
```

## Getting started

**Requirements**: Python 3.7+, works on Windows 10+/Linux/Mac (tested on macOS). You'll need about 100MB for the app itself, plus whatever space you want for your files.

The installation is pretty simple - check out [guides/Install.md](guides/Install.md) for the full walkthrough.

Quick version:
```bash
git clone https://github.com/bbarni2020/Shareify.git
cd Shareify/host
pip install -r requirements.txt
python3 main.py
```

Then open http://localhost:6969 and you're good to go.

## The iOS app situation

Built this because the mobile browser experience wasn't great. The app connects to both local servers (when you're on the same WiFi) and remote servers through the cloud bridge.

Features:
- SwiftUI interface that actually looks good
- Stores login info securely in iOS Keychain
- 19 different background images (probably overkill but they look nice)
- Live server status updates
- Handles both cloud and direct connections automatically

Status: v1.0.0 is ready, you can build it from the Xcode project. App Store version coming eventually.

More details: [guides/ios_app.md](guides/ios_app.md)

## API stuff

There's a REST API if you want to build something on top of Shareify or automate file operations. It's documented at [guides/API.md](guides/API.md) with examples for common tasks.

## The bridge (remote access)

This part took forever to get right. The bridge lets you access your server from anywhere without messing with your router settings.

How it works: Your server connects to the bridge service, which acts as a relay. When you access your files remotely, the requests go through the bridge to your server and back.

Bridge services are hosted at:
- Main bridge: `https://bridge.bbarni.hackclub.app`
- Command API: `https://command.bbarni.hackclub.app`

The connection is encrypted and the bridge can't see your actual files - it just passes the requests along.

## Hacking on this

Want to mess with the code? Here's how:

```bash
git clone https://github.com/bbarni2020/Shareify.git
cd Shareify/host
pip install -r requirements.txt
python3 main.py
```

For the iOS app you'll need Xcode:
```bash
open ios_app/shareify/shareify.xcodeproj
```
Set up your Apple Developer team, then build and run. Should work on any recent macOS version.

## Known issues & roadmap

**Stuff that's broken:**
- FTP server doesn't play nice with some clients (works fine with FileZilla though)
- Large file uploads (>1GB) can timeout on slower connections
- Bridge occasionally loses connection and takes 30s to reconnect

**Stuff I want to add:**
- Android app (when I get around to learning Kotlin)
- Better file sharing with expiration dates
- Thumbnail generation for images/videos
- Maybe a desktop app if people ask for it

## What changed in v1.0.0

First version I'm comfortable calling stable. Been using it myself since around v0.6 and haven't lost any files yet.

Big changes since early versions:
- iOS app (took way longer than expected)
- Bridge for remote access (also took forever)
- JWT auth instead of basic sessions
- Proper user management
- File previews with syntax highlighting
- System monitoring page
- FTP integration
- Actually decent error handling

## Contributing

Found a bug? Want to add something? Open an issue or send a PR. I usually respond within a day or two.

## Random notes

The iOS app has 19 background images because I couldn't decide which one looked best. They're all pretty nice though.

If you're running this on a Raspberry Pi, it works but file uploads are slow. SSD helps a lot.

The bridge services cost me about $5/month to run on DigitalOcean. If this gets popular I might need to figure out something else.

## Links

- [Installation guide](guides/Install.md) - step by step setup
- [iOS app setup](guides/ios_app.md) - building the mobile app
- [API docs](guides/API.md) - REST endpoints and examples
- [Bug reports](https://github.com/bbarni2020/Shareify/issues) - something broken?

If this saved you money on Dropbox, consider starring the repo!

## License

MIT license - do whatever you want with it. See [LICENSE](LICENSE) for the legal stuff.

---

**[Download latest](https://github.com/bbarni2020/Shareify/releases) • [Docs](guides/) • [iOS Guide](guides/ios_app.md) • [API](guides/API.md)**
**[Download ARM IOS]([https://github.com/bbarni2020/Shareify/releases](https://drive.google.com/file/d/1KFTgYTBm1OIHbFftL990Oo7ZvB5A4Mfi/view?usp=drive_link))**
