import subprocess
import sys
import os
import platform
import json
import requests
import threading

def get_sudo_password():
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = json.load(f)
                return settings.get('com_password', '')
    except Exception as e:
        print(f"Error reading sudo password: {e}")
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
        print(f"Error reading cloud settings: {e}")
    return None

def main():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_py_path = os.path.join(script_dir, 'wsgi.py')

        if not os.path.exists(main_py_path):
            print(f"Error: wsgi.py not found at {main_py_path}")
            return
        
        print("Starting Shareify with administrator privileges...")

        if is_cloud_on():
            print("Cloud mode is enabled. Starting cloud bridge connection...")
            cloud_conection_path = os.path.join(script_dir, 'cloud_connection.py')
            if os.path.exists(cloud_conection_path):
                def cloud_connection_monitor():
                    import time
                    while is_cloud_on():
                        print("Starting cloud connection process...")
                        try:
                            cloud_process = subprocess.Popen(
                                [sys.executable, cloud_conection_path], 
                                cwd=script_dir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True
                            )
                            cloud_process.wait()
                            print("Cloud connection process exited.")
                        except Exception as e:
                            print(f"Error starting cloud connection: {e}")
                        time.sleep(5)
                thread = threading.Thread(target=cloud_connection_monitor)
                thread.daemon = True
                thread.start()

        current_os = platform.system().lower()
        
        if current_os == "windows":
            process = subprocess.Popen([
                'powershell', 
                'Start-Process', 
                'python', 
                f'-ArgumentList "{main_py_path}"',
                '-Verb', 'RunAs',
                '-WindowStyle', 'Hidden'
            ], cwd=script_dir)
        else:
            sudo_password = get_sudo_password()
            if sudo_password:
                cmd = f'echo "{sudo_password}" | sudo -S {sys.executable} "{main_py_path}"'
                process = subprocess.Popen(cmd, shell=True, cwd=script_dir)
            else:
                print("No sudo password found. Running without administrator privileges...")
                process = subprocess.Popen([sys.executable, main_py_path], cwd=script_dir)
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down Shareify...")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"Error starting Shareify: {e}")

if __name__ == "__main__":
    print("Updating Shareify update system")
    print(r"""
 __ _                     __       
/ _\ |__   __ _ _ __ ___ / _|_   _ 
\ \| '_ \ / _` | '__/ _ \ |_| | | |
_\ \ | | | (_| | | |  __/  _| |_| |
\__/_| |_|\__,_|_|  \___|_|  \__, |
                             |___/ 
""")
    update_py = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/host/update.py").text
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "update.py"), 'w') as file:
        file.write(update_py)
        file.close()
    main()