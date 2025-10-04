import subprocess
import sys
import os
import platform
import socket
import startup
from pathlib import Path

def create_virtual_environment():
    script_dir = Path(__file__).parent.absolute()
    venv_path = script_dir / "shareify_venv"
    
    print("Creating virtual environment for Shareify...")
    
    if venv_path.exists():
        print("Virtual environment already exists. Removing old one...")
        import shutil
        shutil.rmtree(venv_path)
    
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        print(f"✓ Virtual environment created at: {venv_path}")
        return venv_path
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return None

def get_venv_python(venv_path):
    if platform.system().lower() == "windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def get_venv_pip(venv_path):
    if platform.system().lower() == "windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def install_pip_in_venv(venv_path):
    python_exe = get_venv_python(venv_path)
    try:
        subprocess.check_call([str(python_exe), "-m", "pip", "--version"])
        print("pip is available in virtual environment.")
        return True
    except subprocess.CalledProcessError:
        print("pip not found in virtual environment. Installing...")
        try:
            subprocess.check_call([str(python_exe), "-m", "ensurepip", "--upgrade"])
            print("pip installed successfully in virtual environment.")
            return True
        except Exception as e:
            print(f"Failed to install pip in virtual environment: {e}")
            return False

def upgrade_pip_in_venv(venv_path):
    python_exe = get_venv_python(venv_path)
    try:
        print("Upgrading pip in virtual environment...")
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
        print("pip upgraded successfully in virtual environment.")
    except Exception as e:
        print(f"Failed to upgrade pip in virtual environment: {e}")

def install_requirements_in_venv(venv_path):

    print("Installing requirements in virtual environment...")
    script_dir = Path(__file__).parent.absolute()
    requirements_path = script_dir / 'requirements.txt'
    python_exe = get_venv_python(venv_path)

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False
    
    try:
        print("Installing required packages in virtual environment...")

        with open(requirements_path, 'r') as f:
            packages = f.read().strip().split('\n')
            packages = [pkg.strip() for pkg in packages if pkg.strip()]
        
        print(f"Found {len(packages)} packages to install.")

        for pkg in packages:
            print(f"    - {pkg}")
        
        subprocess.check_call([str(python_exe), "-m", "pip", "install", "-r", str(requirements_path), "--upgrade"])
        print("\n✓ All packages installed successfully in virtual environment.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to install packages in virtual environment: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error occurred during package installation: {e}")
        return False

def check_administrator_privileges():
    current_os = platform.system().lower()
    if current_os == "windows":
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except ImportError:
            return False
    else:
        return os.geteuid() == 0

def main():
    print("=" * 50)
    print("Shareify Installation Script")
    print("=" * 50)

    if not check_administrator_privileges():
        print("Warning: Not running with administrator privileges.")
        print("Some packages might require elevated permissions to install")
        print()
    
    venv_path = create_virtual_environment()
    if not venv_path:
        print("Failed to create virtual environment. Exiting installation...")
        sys.exit(1)
    
    if not install_pip_in_venv(venv_path):
        print("Failed to install pip in virtual environment. Exiting installation...")
        sys.exit(1)
    
    upgrade_pip_in_venv(venv_path)
    print()

    print("Configuring startup...")
    startup.setup_startup(venv_path)
    print("Startup configured successfully.")

    if install_requirements_in_venv(venv_path):
        print("\nInstallation completed successfully!")
        print("Starting the online setup...")
        return
    else:
       print("\nInstallation failed!")
       print("Please check the error messages above and try again.")
       sys.exit(1)
        
main()

import sqlite3
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
import time
import threading
import secrets

app = Flask(__name__, template_folder='web', static_folder='web', static_url_path='/web')

path = ""
password = ""
sudo_password = ""
api_key = secrets.token_hex(32)
db_dir = os.path.join(os.path.dirname(__file__), 'db')
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

if not os.path.exists(os.path.join(os.path.dirname(__file__), 'settings')):
    os.makedirs(os.path.join(os.path.dirname(__file__), 'settings'))

logs_db_path = os.path.join(db_dir, 'logs.db')
users_db_path = os.path.join(db_dir, 'users.db')

def initialize_logs_db():
    conn = sqlite3.connect(logs_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            ip TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def initialize_users_db():
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            ip TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            ip TEXT,
            role TEXT NOT NULL,
            ftp_users TEXT,
            paths TEXT,
            settings TEXT,
            API_KEY TEXT NOT NULL,
            paths_write TEXT
        )
    ''')
    default_user = {
        "username": "admin",
        "password": password,
        "name": "Administrator",
        "ip": "",
        "role": "admin",
        "ftp_users": "",
        "paths": """[""]""",
        "settings": "",
        "API_KEY": api_key,
        "paths_write": """[""]""",
    }
    try:
        cursor.execute('''
            INSERT INTO users (username, password, name, ip, role, ftp_users, paths, settings, API_KEY, paths_write)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (default_user["username"], default_user["password"], default_user["name"], default_user["ip"],
              default_user["role"], default_user["ftp_users"], default_user["paths"], default_user["settings"],
              default_user["API_KEY"], default_user["paths_write"]))
    except sqlite3.IntegrityError:
        print("Default user already exists in the database.")
    conn.commit()
    conn.close()

def create_jsons():
    settings_path = os.path.join(os.path.dirname(__file__), 'settings/settings.json')
    if not os.path.exists(settings_path):
        try:
            settings = requests.get(
                "https://raw.githubusercontent.com/bbarni2020/Shareify/main/current/settings/settings.json"
            )
            settings.raise_for_status()
            settings_json = settings.json()
            settings_json['path'] = path
            settings_json['com_password'] = sudo_password
            with open(settings_path, 'w') as f:
                json.dump(settings_json, f, indent=4)
        except Exception as e:
            print(f"Failed to fetch or write settings.json: {e}")
    roles_path = os.path.join(os.path.dirname(__file__), 'settings/roles.json')
    if not os.path.exists(roles_path):
        try:
            roles = requests.get(
                "https://raw.githubusercontent.com/bbarni2020/Shareify/main/current/settings/roles.json"
            )
            roles.raise_for_status()
            with open(roles_path, 'w') as f:
                f.write(roles.text)
        except Exception as e:
            print(f"Failed to fetch or write roles.json: {e}")

    cloud_path = os.path.join(os.path.dirname(__file__), 'settings/cloud.json')
    if not os.path.exists(cloud_path):
        try:
            with open(cloud_path, 'w') as f:
                f.write("""
{
  "enabled": false
}
""")
        except Exception as e:
            print(f"Failed to fetch or write cloud.json: {e}")

def _list_windows_drives():
    drives = []
    try:
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.isdir(drive):
                drives.append({
                    "name": f"{letter}:",
                    "path": drive
                })
    except Exception:
        pass
    return drives

@app.route('/browse', methods=['GET'])
def browse_directories():
    requested = request.args.get('path', '').strip()
    system_name = platform.system().lower()

    if not requested:
        if system_name == "windows":
            return jsonify({
                "path": None,
                "parent": None,
                "is_root": True,
                "directories": _list_windows_drives()
            })
        requested = '/'

    if system_name == "windows" and len(requested) == 2 and requested[1] == ':':
        requested = f"{requested}\\"

    candidate = Path(requested).expanduser()

    try:
        if system_name != "windows":
            candidate = candidate.resolve()
    except Exception:
        return jsonify({"error": "Directory not accessible"}), 400

    if not candidate.exists() or not candidate.is_dir():
        return jsonify({"error": "Directory not found"}), 404

    try:
        directories = []
        for item in sorted(candidate.iterdir(), key=lambda value: value.name.lower()):
            if item.is_dir():
                directories.append({
                    "name": item.name or str(item),
                    "path": str(item)
                })
    except PermissionError:
        return jsonify({"error": "Permission denied"}), 403
    except Exception:
        return jsonify({"error": "Unable to browse directory"}), 500

    parent_path = None
    if candidate.parent != candidate:
        parent_path = str(candidate.parent)
    elif system_name == "windows" and candidate.anchor:
        parent_path = ''

    response = {
        "path": str(candidate),
        "parent": parent_path,
        "is_root": False,
        "directories": directories
    }

    return jsonify(response)

@app.route('/')
def install_page():
    return render_template('install.html')

@app.route('/set_path', methods=['POST'])
def set_path():
    global path
    path = request.form.get('path')
    if path:
        return redirect(url_for('install_page'))
    return "Path not provided", 400

@app.route('/set_sudo_password', methods=['POST'])
def set_sudo_password():
    global sudo_password
    sudo_password = request.form.get('sudo_password')
    if sudo_password:
        create_jsons()
        return redirect(url_for('install_page'))
    return "Sudo password not provided", 400

@app.route('/set_password', methods=['POST'])
def set_password():
    global password
    password = request.form.get('password')
    if password:
        initialize_logs_db()
        initialize_users_db()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Password not provided'}), 400

@app.route('/complete_installation', methods=['POST'])
def complete_installation():
    try:
        script_dir = Path(__file__).parent.absolute()
        launcher_path = script_dir / 'launcher.py'
        venv_path = script_dir / 'shareify_venv'
        
        if launcher_path.exists():
            if venv_path.exists():
                python_exe = get_venv_python(venv_path)
            else:
                python_exe = sys.executable
                
            subprocess.Popen([str(python_exe), str(launcher_path)])
            def shutdown_installer():
                time.sleep(2)
                os._exit(0)
            
            threading.Thread(target=shutdown_installer, daemon=True).start()
            
            return jsonify({'success': True, 'message': 'Installation complete! Starting Shareify...'})
        else:
            return jsonify({'success': False, 'error': 'Launcher not found'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

def create_app():
    initialize_logs_db()
    initialize_users_db()
    return app

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    
    host = '0.0.0.0'
    port = 6969
    local_ip = get_local_ip()
    
    application = create_app()
    server = make_server(host, port, application)
    print(f"Starting installation server at: http://{host}:{port}")
    print(f"Access the page from network at:  http://{local_ip}:{port}")
    server.serve_forever()