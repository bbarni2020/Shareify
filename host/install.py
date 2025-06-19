import subprocess
import sys
import os
import platform

def install_pip():
    try:
        import pip
        print("pip is already installed.")
    except ImportError:
        print("pip not found. Installing pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
            print("pip installed successfully.")
        except Exception as e:
            print(f"Failed to install pip: {e}")
            return False
    return True

def upgrade_pip():
    try:
        print("Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgarde", "pip"])
        print("pip upgraded successfully.")
    except Exception as e:
        print(f"Falied to upgrade pip: {e}")

def install_requirements():
    print("Installing requirements...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_path = os.path.join(script_dir, 'requirements.txt')

    if not os.path.exists(requirements_path):
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False
    
    try:
        print("Installing required packages...")

        with open(requirements_path, 'r') as f:
            packages = f.read().strip().split('\n')
            packages = [pkg.strip() for pkg in packages if pkg.strip()]
        
        print(f"Found {len(packages)} packages to install.")

        for pkg in packages:
            print(F"    - {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path, "--upgrade"])
        print("\n✓ All packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Failed to install packages: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error occurred: {e}")
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
    
    if not install_pip():
        print("Failed to install pip. Exciting installation...")
        sys.exit(1)
    
    upgrade_pip()
    print()

    if install_requirements():
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
                "https://raw.githubusercontent.com/bbarni2020/Shareify/main/host/settings/settings.json"
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
                "https://raw.githubusercontent.com/bbarni2020/Shareify/main/host/settings/roles.json"
            )
            roles.raise_for_status()
            with open(roles_path, 'w') as f:
                f.write(roles.text)
        except Exception as e:
            print(f"Failed to fetch or write roles.json: {e}")

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
        launcher_path = os.path.join(os.path.dirname(__file__), 'launcher.py')
        if os.path.exists(launcher_path):
            subprocess.Popen([sys.executable, launcher_path])
            def shutdown_installer():
                time.sleep(2)
                os._exit(0)
            
            threading.Thread(target=shutdown_installer, daemon=True).start()
            
            return jsonify({'success': True, 'message': 'Installation complete! Starting Shareify...'})
        else:
            return jsonify({'success': False, 'error': 'Launcher not found'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 6969
    print(f"Starting installation server at http://{host}:{port}")
    app.run(host=host, port=port, debug=True)