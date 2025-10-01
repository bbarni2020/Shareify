# Getting Shareify Running

So you want to set up your own NAS? Cool. This thing started as my weekend project because I was tired of paying for cloud storage and wanted something simple that just works.

## What you'll need

Honestly, if your computer can run a web browser, it can probably run this. But here's the breakdown:

**Your machine needs:**
- At least 512MB RAM (though 2GB+ is way better - learned this the hard way)
- 100MB free space + whatever you're planning to store
- Python 3.7 or newer (I test with 3.9+, older versions might be cranky)
- Internet connection to grab dependencies

**OS-wise:**
- Windows 10/11 - works fine
- macOS 10.14+ - my daily driver, so this gets the most love
- Linux - tested on Ubuntu 18.04+, should work on most distros

You'll also want admin/sudo access for the setup. Trust me on this one.

## Before we start

Quick sanity check:
1. Run `python3 --version` - you should see 3.7 or higher
2. Make sure you can connect to the internet
3. Pick a folder where you want this thing to live
4. Think about where you want to store your actual files (this becomes your NAS root)
5. Have your admin password handy

## Installation

### Getting the files

**Option 1: One-liner (works everywhere)**

macOS/Linux/WSL:
```bash
curl -L "https://github.com/bbarni2020/Shareify/releases/latest/download/Shareify.zip" -o Shareify.zip
```

Windows (PowerShell):
```powershell
Invoke-WebRequest -Uri "https://github.com/bbarni2020/Shareify/releases/latest/download/Shareify.zip" -OutFile "Shareify.zip"
```

**Option 2: If that fails for some reason**

Extract the download URL manually:
```bash
curl -s https://api.github.com/repos/bbarni2020/Shareify/releases/latest | grep '"browser_download_url"' | cut -d '"' -f 4 | xargs curl -L -o Shareify.zip
```

**Option 3: Just download it like a normal person**
1. Go to https://github.com/bbarni2020/Shareify/releases/latest
2. Download Shareify.zip
3. Done

**Unzip it:**

Windows:
```cmd
powershell Expand-Archive -Path Shareify.zip -DestinationPath .
```

Everything else:
```bash
unzip Shareify.zip
cd Shareify
```

### Run the installer

This is the easy part:
```bash
python3 install.py
```

If it freezes for a long time, press Ctrl+C to continue.  


The script does a bunch of stuff automatically:
- Checks if pip is installed (installs it if missing)
- Updates pip to latest version
- Installs all the Python packages we need
- Sets up the database
- Starts a web server on port 6969 for configuration

You'll see something like this if it works:
```
==================================================
Shareify Installation Script
==================================================
pip is already installed.
Upgrading pip...
✓ All packages installed successfully.

Installation completed successfully!
Starting the online setup...
Starting installation server at: http://0.0.0.0:6969
```

### Web setup

Once the installer finishes, open your browser and go to:
- Same machine: `http://127.0.0.1:6969`
- From another device: `http://[your-ip]:6969`

The installer will show you both URLs.

## Configuration

The web interface walks you through 3 things:

**1. NAS Storage Path**
This is where your files will live. Pick a folder that:
- Already exists (create it first if needed)
- Has enough space for your stuff
- You have write access to

Examples:
- Linux: `/home/yourname/nas` or `/mnt/storage`
- macOS: `/Users/Shared/NAS` 
- Windows: `D:\NAS` or wherever

**2. System Admin Password**
Just use your current admin/sudo password. We need this for system stuff like updates. It stays local, never gets sent anywhere.

**3. NAS Admin Account**
Create a username/password for accessing the NAS web interface. This is separate from your system password.

Click "Complete Installation" and you're done!

## Post-Install

The installer shuts itself down and starts the actual NAS server. You'll get a new URL to access your NAS interface.

Log in with the admin account you just created and start uploading files.

## When things go wrong

**Download fails:**
Try the manual download from GitHub releases page, or use this as backup:
```bash
wget "https://github.com/bbarni2020/Shareify/releases/latest/download/Shareify.zip"
```

**"Permission denied" errors:**
```bash
sudo python3 install.py
```

**Port 6969 is busy:**
```bash
lsof -ti:6969 | xargs kill -9
```
Then try again.

**Python not found:**
Make sure Python 3.7+ is installed and in your PATH.

**Can't access the web interface:**
Check your firewall - might need to allow port 6969 temporarily.

**Database errors:**
Make sure the folder you're installing to is writable:
```bash
chmod 755 /path/to/shareify
```

## Security notes

- Use strong passwords (duh)
- The setup server (port 6969) only runs during installation
- Your admin password stays on your machine
- Consider firewall rules for the main server after setup

## That's it

If everything worked, you now have your own NAS server. The web interface should be pretty self-explanatory from here.

Hit me up if you run into issues - there's probably something I missed in the docs.
