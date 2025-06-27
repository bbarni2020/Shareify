# Shareify Installation Guide

## Prerequisites

- Python 3.7 or higher
- Administrator/root privileges (recommended)
- Internet connection for downloading dependencies

## Installation Steps

### 1. Download Shareify
```bash
curl -s https://api.github.com/repos/bbarni2020/Shareify/releases/latest \ | jq -r '.assets[] | select(.name == "Shareify.zip") | browser_download_url' \ | xargs curl -L -o Shareify.zip
```
Unzip the file and open host folder.

### 2. Run the Installation Script
```bash
python3 install.py
```

The script will automatically:

- Check and install pip if needed
- Upgrade pip to the latest version
- Install all required dependecies from requirements.txt
- Start the web-based setup server

### 3. Web-based Setup
After running the installation script, you'll see:

```
Starting installation server at http://0.0.0.0:6969
```

Open your web browser and navigate to the given network ip and port.

### 4. Configure Shareify
On the web interface, you'll need to provide:
1. File Path: Set the directory path you want to share
- Example: /home/user/shared (Linux/Mac) or C:\Users\Username\Documents
2. System password: Enter your system administrator password
- This is used for system-level operations such as updateing. This is only stored locally on your device