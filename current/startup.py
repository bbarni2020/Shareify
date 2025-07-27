import subprocess
import os
import sys
from pathlib import Path

def setup_startup():
    current_dir = Path(__file__).parent.absolute()
    launcher_path = current_dir / "launcher.py"
    
    if sys.platform == "darwin":
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.shareify.launcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{launcher_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{current_dir}</string>
</dict>
</plist>"""
        
        plist_path = Path.home() / "Library/LaunchAgents/com.shareify.launcher.plist"
        plist_path.parent.mkdir(exist_ok=True)
        
        with open(plist_path, "w") as f:
            f.write(plist_content)
        
        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True)
        
    elif sys.platform.startswith("linux"):
        service_content = f"""[Unit]
Description=Shareify Launcher Service
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={current_dir}
ExecStart=/usr/bin/python3 {launcher_path}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        
        service_path = Path("/etc/systemd/system/shareify-launcher.service")
        
        try:
            with open(service_path, "w") as f:
                f.write(service_content)
            
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "shareify-launcher.service"], check=True)
            subprocess.run(["systemctl", "start", "shareify-launcher.service"], check=True)
        except PermissionError:
            print("Need sudo privileges to install system service")
            
    elif sys.platform == "win32":
        startup_folder = Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
        bat_content = f"""@echo off
cd /d "{current_dir}"
python "{launcher_path}"
"""
        
        bat_path = startup_folder / "shareify_launcher.bat"
        with open(bat_path, "w") as f:
            f.write(bat_content)