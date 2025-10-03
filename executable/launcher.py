import subprocess
import sys
import os
import platform
import json
import requests
try:
    import update
except ImportError:
    import update
import threading
from pathlib import Path

def get_venv_python():
    script_dir = Path(__file__).parent.absolute()
    venv_path = script_dir / 'shareify_venv'
    if venv_path.exists():
        if platform.system().lower() == 'windows':
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
        if python_exe.exists():
            return str(python_exe)
    return sys.executable

def get_sudo_password():
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                return settings.get('com_password', '')
    except Exception as e:
        print(f'Error reading sudo password: {e}')
    return None

def is_cloud_on():
    try:
        cloud_path = os.path.join(os.path.dirname(__file__), 'settings', 'cloud.json')
        if os.path.exists(cloud_path):
            with open(cloud_path, 'r') as f:
                settings = json.load(f)
                if settings.get('enabled', ''):
                    return True
                else:
                    return False
    except Exception as e:
        print(f'Error reading cloud settings: {e}')
    return None

def main():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        executable_path = os.path.join(script_dir, 'shareify.exe')
        if os.path.exists(executable_path):
            print('Starting Shareify executable...')
            current_os = platform.system().lower()
            if current_os == 'windows':
                process = subprocess.Popen(['powershell', 'Start-Process', executable_path, '-Verb', 'RunAs', '-WindowStyle', 'Hidden'], cwd=script_dir)
            else:
                sudo_password = get_sudo_password()
                if sudo_password:
                    cmd = f'echo "{sudo_password}" | sudo -S "{executable_path}"'
                    process = subprocess.Popen(cmd, shell=True, cwd=script_dir)
                else:
                    print('No sudo password found. Running without administrator privileges...')
                    process = subprocess.Popen([executable_path], cwd=script_dir)
        else:
            main_py_path = os.path.join(script_dir, 'wsgi.py')
            python_exe = get_venv_python()
            if not os.path.exists(main_py_path):
                print(f'Error: wsgi.py not found at {main_py_path}')
                return
            print(f'Starting Shareify with Python: {python_exe}')
            current_os = platform.system().lower()
            if current_os == 'windows':
                process = subprocess.Popen(['powershell', 'Start-Process', python_exe, f'-ArgumentList "{main_py_path}"', '-Verb', 'RunAs', '-WindowStyle', 'Hidden'], cwd=script_dir)
            else:
                sudo_password = get_sudo_password()
                if sudo_password:
                    cmd = f'echo "{sudo_password}" | sudo -S {python_exe} "{main_py_path}"'
                    process = subprocess.Popen(cmd, shell=True, cwd=script_dir)
                else:
                    print('No sudo password found. Running without administrator privileges...')
                    process = subprocess.Popen([python_exe, main_py_path], cwd=script_dir)
        if is_cloud_on():
            print('Cloud mode is enabled. Starting cloud bridge connection...')
            cloud_conection_path = os.path.join(script_dir, 'cloud_connection.py')
            if os.path.exists(cloud_conection_path):

                def cloud_connection_monitor():
                    import time
                    while is_cloud_on():
                        print('Starting cloud connection process...')
                        try:
                            cloud_process = subprocess.Popen([get_venv_python(), cloud_conection_path], cwd=script_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                            cloud_process.wait()
                            print('Cloud connection process exited.')
                        except Exception as e:
                            print(f'Error starting cloud connection: {e}')
                        time.sleep(5)
                thread = threading.Thread(target=cloud_connection_monitor)
                thread.daemon = True
                thread.start()
        process.wait()
    except KeyboardInterrupt:
        print('\nShutting down Shareify...')
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f'Error starting Shareify: {e}')
if __name__ == '__main__':
    print('Updating Shareify update system')
    print("\n __ _                     __       \n/ _\\ |__   __ _ _ __ ___ / _|_   _ \n\\ \\| '_ \\ / _` | '__/ _ \\ |_| | | |\n_\\ \\ | | | (_| | | |  __/  _| |_| |\n\\__/_| |_|\\__,_|_|  \\___|_|  \\__, |\n                             |___/ \n")
    update_py = requests.get('https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/update.py').text
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update.py'), 'w') as file:
        file.write(update_py)
        file.close()
    main()