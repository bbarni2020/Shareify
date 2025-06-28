# Shareify Installation Guide

Welcome to the comprehensive installation guide for Shareify. This guide will walk you through every step of the installation process, from initial setup to final configuration.

## System Requirements

Before beginning the installation, ensure your system meets the following requirements:

### Hardware Requirements
- **RAM**: Minimum 512MB, recommended 2GB or more
- **Storage**: At least 100MB free space for the application, plus additional space for shared files
- **Network**: Ethernet or Wi-Fi connection for network access
- **Processor**: Any modern processor (x86, x64, ARM supported)

### Software Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- **Python**: Version 3.7 or higher (Python 3.9+ recommended for optimal performance)
- **Internet Connection**: Required for downloading dependencies and server management features
- **Web Browser**: Modern browser (Chrome 80+, Firefox 75+, Safari 13+, Edge 80+)

### Permissions
- **Administrator/Root Privileges**: Highly recommended for system-level operations
- **Network Access**: The system should be able to bind to network ports
- **File System Access**: Read/write permissions for the installation directory and NAS storage locations

## Pre-Installation Checklist

Before starting the installation, complete the following steps:

1. **Verify Python Installation**: Open a terminal or command prompt and run `python3 --version` to confirm Python 3.7+ is installed
2. **Check Network Connectivity**: Ensure your system can access the internet for downloading dependencies
3. **Prepare Installation Directory**: Choose a location where you want to install Shareify (ensure sufficient disk space)
4. **Plan NAS Storage Structure**: Decide which directories you want to manage and ensure they exist
5. **Gather System Information**: Have your system administrator password ready for the setup process

## Installation Process

### Step 1: Download Shareify

#### Option A: Using curl (Linux/macOS)
```bash
curl -s https://api.github.com/repos/bbarni2020/Shareify/releases/latest | jq -r '.assets[] | select(.name == "Shareify.zip") | .browser_download_url' | xargs curl -L -o Shareify.zip
```

#### Option B: Using wget (Linux)
```bash
wget $(curl -s https://api.github.com/repos/bbarni2020/Shareify/releases/latest | jq -r '.assets[] | select(.name == "Shareify.zip") | .browser_download_url') -O Shareify.zip
```

#### Option C: Manual Download
1. Visit the GitHub releases page: https://github.com/bbarni2020/Shareify/releases/latest
2. Download the latest Shareify.zip file
3. Save it to your desired installation directory

#### Extracting the Files
After downloading, extract the ZIP file:

**Windows:**
```cmd
powershell Expand-Archive -Path Shareify.zip -DestinationPath .
```

**Linux/macOS:**
```bash
unzip Shareify.zip
```

Navigate to the extracted folder and enter the `host` directory:
```bash
cd Shareify/host
```

### Step 2: Run the Installation Script

The installation script will handle all dependency management and initial setup. Execute the script using Python:

```bash
python3 install.py
```

#### What the Installation Script Does

The script performs several critical tasks in sequence:

1. **Pip Verification and Installation**: Checks if pip (Python package installer) is available on your system. If not found, it automatically installs pip using Python's built-in ensurepip module.

2. **Pip Upgrade**: Updates pip to the latest version to ensure compatibility with all required packages and to benefit from the latest security updates and features.

3. **Dependencies Installation**: Reads the requirements.txt file and installs all necessary Python packages including:
   - Flask: Web framework for the server
   - Flask-SocketIO: Real-time communication support
   - SQLite3: Database management
   - Bcrypt: Password hashing and security
   - Requests: HTTP library for external communications
   - And other essential dependencies

4. **System Privilege Check**: Verifies if the script is running with administrator privileges and warns if elevated permissions are not available.

5. **Database Initialization**: Creates the necessary SQLite database files for user management and system logging.

6. **Web Server Startup**: Launches the installation web interface on port 6969 for the configuration phase.

#### Expected Output
You should see output similar to:
```
==================================================
Shareify Installation Script
==================================================
pip is already installed.
Upgrading pip...
pip upgraded successfully.

Installing requirements...
Found 15 packages to install.
    - Flask==2.3.3
    - Flask-SocketIO==5.3.6
    - bcrypt==4.0.1
    - requests==2.31.0
    - [additional packages...]

✓ All packages installed successfully.

Installation completed successfully!
Starting the online setup...
Starting installation server at: http://0.0.0.0:6969
Access the page from network at: http://192.168.1.100:6969
```

### Step 3: Web-Based Configuration

After the installation script completes, it will start a web server for the configuration phase. The server will display two URLs:

- **Local Access**: `http://0.0.0.0:6969` or `http://127.0.0.1:6969`
- **Network Access**: `http://[your-local-ip]:6969`

Open your web browser and navigate to the appropriate URL. If you're configuring from the same machine, use the local address. If you're configuring from another device on the network, use the network address.

#### Configuration Interface

The web interface presents a clean, step-by-step configuration wizard:

### Step 4: Configure Shareify Settings

#### 4.1 NAS Storage Path Configuration

The first configuration step involves setting up the root directory for NAS storage management.

**What to Enter:**
- The absolute path to the directory you want to manage as NAS storage
- This directory will become the root of your NAS file system
- All files and subdirectories within this path will be accessible through the Shareify NAS interface

**Path Examples:**
- **Linux**: `/mnt/nas/storage` or `/var/shareify/nas`
- **macOS**: `/Volumes/NAS/Storage` or `/Users/Shared/NAS`
- **Windows**: `D:\NAS\Storage` or `C:\ShareifyNAS`

**Important Considerations:**
- Ensure the path exists before entering it
- The user running Shareify must have read/write permissions to this directory
- Consider the available disk space and future storage expansion needs
- Avoid using system directories or sensitive locations
- For external drives, ensure they are properly mounted before installation

#### 4.2 System Administrator Password

This password is used for system-level operations and NAS management tasks.

**Security Information:**
- This password is stored locally on your server only
- It's encrypted using industry-standard encryption methods
- Used for automatic updates and system maintenance tasks
- Never transmitted over the network

**Password Requirements:**
- Use your current system administrator password
- On Windows: Your Windows admin account password
- On Linux/macOS: Your sudo password
- Ensure the password is current and correct

#### 4.3 Shareify NAS Admin Account

Create the main administrative account for NAS management.

**Account Details:**
- **Username**: Defaults to "admin" (can be changed later)
- **Password**: Create a strong password for NAS management interface access
- **Role**: Automatically set to administrator with full system access

**Password Recommendations:**
- Minimum 8 characters
- Include uppercase and lowercase letters
- Include numbers and special characters
- Avoid common dictionary words
- Don't reuse passwords from other services

### Step 5: Complete Installation

After providing all required information, click the "Complete Installation" button to finalize the setup.

#### Final Installation Steps

The system will:
1. **Create Configuration Files**: Generate all necessary JSON configuration files with your settings
2. **Initialize Databases**: Set up user management and logging databases with your admin account
3. **Validate Settings**: Verify all paths and credentials are correct
4. **Launch Main Server**: Start the primary Shareify NAS server
5. **Cleanup**: Terminate the installation server and clean up temporary files

#### Success Confirmation

Upon successful completion, you'll see:
```
Installation complete! Starting Shareify...
```

The installation window will close automatically, and the main Shareify NAS server will start.

## Post-Installation

After successful installation:
1. The installer will automatically launch the main Shareify NAS server
2. Access the management interface at the provided IP address (displayed in the terminal)
3. Log in with the admin credentials you created during installation
4. Your Shareify NAS server is now ready to use

## Troubleshooting Installation Issues

### Installation Fails with Permission Errors
**Solution**: Run the installation script with elevated privileges:
```bash
sudo python3 install.py
```

### Port 6969 Already in Use
**Solution**: Kill the process using the port or wait for it to become available:
```bash
lsof -ti:6969 | xargs kill -9
```

### Python Not Found
**Solution**: Install Python 3.7+ or check your PATH configuration:
```bash
which python3
python3 --version
```

### Cannot Access Web Interface
**Solution**: Check firewall settings and ensure the port is open:
```bash
sudo ufw allow 6969
```

### Database Connection Errors
**Solution**: Ensure the installation directory has proper write permissions:
```bash
chmod 755 /path/to/shareify
```

### Dependencies Installation Fails
**Solution**: Try installing dependencies manually:
```bash
pip3 install -r requirements.txt --user
```

### Web Server Won't Start
**Solution**: Check if another service is using the port and ensure Python has network permissions:
```bash
netstat -tlnp | grep :6969
```

## Installation Security Notes

During installation, keep these security considerations in mind:

- **Password Security**: Use strong, unique passwords for both system and Shareify NAS admin accounts
- **File Permissions**: Ensure the installation directory has appropriate read/write permissions
- **Network Security**: The installation server (port 6969) is only needed during setup and will automatically shut down after completion
- **Firewall**: Consider temporarily allowing port 6969 during installation, then remove the rule after completion

## Conclusion

Congratulations! You have successfully installed Shareify NAS. Your network-attached storage server is now ready to use. The installation process has set up all necessary components, created your admin account, and configured the basic system settings.

Your Shareify NAS server will start automatically after installation completion. Check your terminal for the server address and use your admin credentials to log in and begin managing your NAS storage.