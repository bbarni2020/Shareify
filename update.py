import requests
import os
import json
import sqlite3
import threading
from time import sleep
import sys
import shutil
import tempfile

GITHUB_OWNER = "bbarni2020"
GITHUB_REPO = "Shareify"
GITHUB_BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/refs/heads/{GITHUB_BRANCH}"

FILES_TO_UPDATE = [
    "main.py",
    "database.py",
    "cloud_connection.py",
    "install.py",
    "launcher.py",
    "startup.py",
    "wsgi.py",
    "venv_manager.py",
    "update.py",
    "requirements.txt",
    "crypto_manager.py",
    "hash_passwords.py",
    "web/index.html",
    "web/index.css",
    "web/install.html",
    "web/login.html",
    "web/login.css",
    "web/login.js",
    "web/endpoints.json"
]

def is_admin():
    try:
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def relaunch_as_admin():
    if os.name == 'nt':
        import ctypes
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    else:
        os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
    sys.exit(0)

if os.environ.get('ENABLE_UPDATES','true').lower()!='true':
    print('Updates disabled')
    sys.exit(1)
if not is_admin():
    print("update.py is not running as administrator/root. Trying to relaunch as admin/root...")
    relaunch_as_admin()

def load_settings(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                settings = json.load(file)
                return settings
            except json.JSONDecodeError:
                print("Error: Invalid JSON format in settings file.")
    else:
        print(f"Settings file '{file_path}' not found.")
        exit(1)

settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings/settings.json")
settings = load_settings(settings_file)

def get_admin_api_key():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db/users.db")
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT API_KEY FROM users WHERE role = 'admin' LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        print(f"Error getting admin API key: {e}")
    return None

def shutdown_server():
    try:
        api_key = get_admin_api_key()
        if api_key:
            import jwt
            payload = {'user_id': 1, 'username': 'admin'}
            token = jwt.encode(payload, os.environ.get('JWT_SECRET_KEY', 'default_secret'), algorithm='HS256')
            requests.post(
                f"http://localhost:{settings['port']}/update_start_exit_program",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            sleep(2)
    except Exception as e:
        print(f"Unable to shutdown server gracefully: {e}")

def fetch_remote_version():
    try:
        response = requests.get(f"{BASE_URL}/info/version", timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        print(f"Error fetching remote version: {e}")
        return None

def download_file(relative_path):
    url = f"{BASE_URL}/current/{relative_path}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content if relative_path.endswith(('.png', '.jpg', '.ico', '.woff', '.woff2', '.ttf')) else response.text
    except Exception as e:
        print(f"Failed to download {relative_path}: {e}")
        return None

def backup_current_files(backup_dir):
    host_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        for file_path in FILES_TO_UPDATE:
            source = os.path.join(host_dir, file_path)
            if os.path.exists(source):
                dest = os.path.join(backup_dir, file_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(source, dest)
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def restore_from_backup(backup_dir):
    host_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        for file_path in FILES_TO_UPDATE:
            source = os.path.join(backup_dir, file_path)
            if os.path.exists(source):
                dest = os.path.join(host_dir, file_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(source, dest)
        print("Restored from backup")
        return True
    except Exception as e:
        print(f"Restore failed: {e}")
        return False

def apply_updates(temp_dir):
    host_dir = os.path.dirname(os.path.abspath(__file__))
    updated_files = []
    
    try:
        for file_path in FILES_TO_UPDATE:
            print(f"Updating {file_path}...")
            content = download_file(file_path)
            if content is None:
                print(f"Warning: Could not download {file_path}, skipping")
                continue
            
            dest_path = os.path.join(host_dir, file_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            mode = 'wb' if isinstance(content, bytes) else 'w'
            encoding = None if isinstance(content, bytes) else 'utf-8'
            
            with open(dest_path, mode, encoding=encoding) as f:
                f.write(content)
            
            updated_files.append(file_path)
        
        return True, updated_files
    except Exception as e:
        print(f"Update failed: {e}")
        return False, updated_files

def update_version_in_settings(new_version):
    try:
        with open(settings_file, 'r') as f:
            current_settings = json.load(f)
        
        current_settings['version'] = new_version
        
        with open(settings_file, 'w') as f:
            json.dump(current_settings, f, indent=4)
        
        print(f"Updated version to {new_version}")
        return True
    except Exception as e:
        print(f"Failed to update version: {e}")
        return False

def run_main():
    main_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    os.system(f'python3 "{main_path}"')

def update():
    current_version = settings.get('version', 'unknown')
    print(f"Current version: {current_version}")
    
    remote_version = fetch_remote_version()
    if not remote_version:
        print("Could not fetch remote version. Update aborted.")
        exit(1)
    
    print(f"Remote version: {remote_version}")
    
    if remote_version == current_version:
        print("You are already using the latest version.")
        exit(0)
    
    print("New version available. Starting update process...")
    
    shutdown_server()
    
    backup_dir = tempfile.mkdtemp(prefix='shareify_backup_')
    print(f"Creating backup in {backup_dir}")
    
    if not backup_current_files(backup_dir):
        print("Backup failed. Update aborted.")
        exit(1)
    
    print("Downloading and applying updates...")
    success, updated_files = apply_updates(backup_dir)
    
    if not success:
        print("Update failed. Restoring from backup...")
        restore_from_backup(backup_dir)
        shutil.rmtree(backup_dir, ignore_errors=True)
        print("Restore complete. Restarting server...")
        sleep(3)
        t = threading.Thread(target=run_main)
        t.start()
        exit(1)
    
    print(f"Successfully updated {len(updated_files)} files")
    
    if update_version_in_settings(remote_version):
        print("Version updated successfully")
    
    try:
        shutil.rmtree(backup_dir, ignore_errors=True)
    except:
        pass
    
    print("Update completed successfully!")
    print("Restarting server in 5 seconds...")
    sleep(5)
    
    t = threading.Thread(target=run_main)
    t.start()
    exit(0)

if __name__ == "__main__":
    update()