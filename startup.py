import subprocess
import os
import sys
from pathlib import Path

def get_venv_python(venv_path):
    import platform
    if platform.system().lower() == "windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def setup_startup(venv_path=None):
    current_dir = Path(__file__).parent.absolute()
    launcher_path = current_dir / "launcher.py"
    
    if venv_path and venv_path.exists():
        python_exe = get_venv_python(venv_path)
        if not python_exe.exists():
            print(f"Warning: Virtual environment Python not found at {python_exe}, using system Python")
            python_exe = "/usr/bin/python3"
    else:
        python_exe = "/usr/bin/python3"
    
    if sys.platform == "darwin":
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.shareify.launcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{launcher_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>{current_dir}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>VIRTUAL_ENV</key>
        <string>{venv_path if venv_path else ''}</string>
    </dict>
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
Environment=VIRTUAL_ENV={venv_path if venv_path else ''}
ExecStart={python_exe} {launcher_path}
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
        
        if venv_path and venv_path.exists():
            win_python_exe = venv_path / "Scripts" / "python.exe"
            if not win_python_exe.exists():
                win_python_exe = "python"
        else:
            win_python_exe = "python"
            
        bat_content = f"""@echo off
cd /d "{current_dir}"
set VIRTUAL_ENV={venv_path if venv_path else ''}
"{win_python_exe}" "{launcher_path}"
"""
        
        bat_path = startup_folder / "shareify_launcher.bat"
        with open(bat_path, "w") as f:
            f.write(bat_content)