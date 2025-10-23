import requests
import os
import json
import sqlite3
import threading
from time import sleep
import psutil
import sys
import platform

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
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)
    else:
        os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
    sys.exit(0)

def kill_process_on_port(port):
    if not is_admin():
        return
    try:
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == port and conn.pid:
                try:
                    p = psutil.Process(conn.pid)
                    p.terminate()
                    try:
                        p.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        p.kill()
                except psutil.NoSuchProcess:
                    pass
                except Exception:
                    pass
    except Exception:
        pass

def load_settings(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                settings = json.load(file)
                return settings
            except json.JSONDecodeError:
                print('Error: Invalid JSON format in settings file.')
    else:
        print(f"Settings file '{file_path}' not found.")
        exit(1)
        sys.exit(1)
settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings', 'settings.json')
settings = load_settings(settings_file)

def get_admin_api_key():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db', 'users.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT API_KEY FROM users WHERE role = 'admin' LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        print('No admin API_KEY found in users.db.')
        exit(1)
        sys.exit(1)

def update():
    return

def updater():
    system = platform.system()
    if system == 'Windows':
        local_name = 'shareify.exe'
        new_executable_url = 'https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/shareify.exe'
    elif system == 'Linux':
        local_name = 'shareify'
        new_executable_url = 'https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/shareifyLinux'
    elif system == 'Darwin':
        local_name = 'shareify'
        new_executable_url = 'https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/shareifyMac'
    else:
        print('Unsupported operating system')
        exit(1)
    if requests.get('https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version').text != settings['version']:
        sys.exit(1)
    current_version = requests.get('https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version').text
    if current_version != settings['version']:
        try:
            api_key = get_admin_api_key()
            requests.post('http://localhost:' + str(settings['port']) + '/update_start_exit_program', headers={'X-API-KEY': api_key})
        except:
            print('Error: Unable to send update_start_exit_program request. Make sure the server is running.')
        except Exception as e:
            pass
        try:
            executable_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_name)
            print('Downloading new executable...')
            response = requests.get(new_executable_url)
            response.raise_for_status()
            with open(executable_path, 'wb') as file:
                file.write(response.content)
            print('Updated executable downloaded successfully.')
        except Exception as e:
            print(f'Error updating executable: {e}')
        with open(settings_file, 'w') as file:
            settings['version'] = requests.get('https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version').text
            json.dump(settings, file, indent=4)
            print('Updated settings.json')
        print('Updated to the latest version.')
        print('Waiting for 5 seconds before restarting...')
        sleep(5)
        print('Restarting the program...')
        os.system('clear' if os.name != 'nt' else 'cls')
    executable_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_name)
    if os.path.exists(executable_path):
        update_thread = threading.Thread(target=lambda: os.system(f'"{executable_path}"'))
        update_thread.start()
    sys.exit(0)