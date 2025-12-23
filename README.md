# Shareify Executable Readme

**Self-hosted file server in a single executable.**

This is the standalone version of Shareify - no Python setup required, just download and run.

## System Requirements

- **Windows 10+**, **macOS 10.14+**, or **any Linux distro** (x86_64)
- Admin/sudo privileges for initial setup
- About 50MB disk space
- Internet connection for remote access features

The Linux build uses StaticX so it'll work on basically anything - old Ubuntu, fresh Arch, whatever.

## Quick Start

1. Extract this zip wherever you want Shareify to live
2. Run the executable:
   - Windows: Double-click `shareify.exe`
   - Mac: `./shareify` in terminal
   - Linux: `chmod +x shareify && ./shareify`
3. If prompted for admin/sudo, allow it - just for initial setup
4. Open your browser to `http://localhost:6969`

## Default Login

**Username:** `admin`  
**Password:** `root`

⚠️ **Change these immediately** in the settings panel unless you want strangers browsing your files.

## What's Included

- Web interface for file management
- Bridge connection for remote access
- Built-in FTP server
- User management system
- File sharing capabilities

No external dependencies - everything's bundled in.

## Troubleshooting

**Can't connect to localhost:6969?**
- Check if another app is using port 6969
- Try running as administrator/sudo

**Linux: "error while loading shared libraries"?**
- Shouldn't happen with StaticX but if it does, try `ldd shareify` to see what's missing
- Worst case, build from source

**Files not uploading?**
- Make sure you have write permissions to the Shareify folder
- Check available disk space

**Remote access not working?**
- Verify internet connection
- Bridge service might be down (rare but happens)

## Need Help?

Something broken? Found a bug? 

- [Open an issue](https://github.com/bbarni2020/Shareify/issues)
- Check the [full documentation](https://github.com/bbarni2020/Shareify)

No promises, but I usually respond pretty quick.
