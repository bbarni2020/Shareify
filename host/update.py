import requests
import os
import json
import sqlite3
import threading
from time import sleep
import sys

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

def kill_process_on_port(port):
    return

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
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT API_KEY FROM users WHERE role = 'admin' LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        print("No admin API_KEY found in users.db.")
        exit(1)

def run_main():
    os.system(f'python3 "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")}"')

def update():
    if requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version").text != settings['version']:
        try:
            api_key = get_admin_api_key()
            requests.post(
                "http://localhost:" + str(settings['port']) + "/update_start_exit_program",
                headers={"X-API-KEY": api_key}
            )
        except:
            print("Error: Unable to send update_start_exit_program request. Make sure the server is running.")
            pass
        new_update = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/main.py").text
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"), 'w') as file:
            file.write(new_update)
            file.close()
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
        index_html = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/web/index.html").text
        with open(os.path.join(web_dir, "index.html"), 'w') as file:
            file.write(index_html)
            file.close()
        install_html = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/web/install.html").text
        with open(os.path.join(web_dir, "install.html"), 'w') as file:
            file.write(install_html)
            file.close()
        endpoints_json = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/web/endpoints.json").text
        with open(os.path.join(web_dir, "endpoints.json"), 'w') as file:
            file.write(endpoints_json)
            file.close()
        install_py = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/web/install.py").text
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "install.py"), 'w') as file:
            file.write(install_py)
            file.close()
        index_css = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/web/index.css").text
        with open(os.path.join(web_dir, "index.css"), 'w') as file:
            file.write(index_css)
            file.close()
        login_html = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/web/login.html").text
        with open(os.path.join(web_dir, "login.html"), 'w') as file:
            file.write(login_html)
            file.close()
        database_py = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/database.py").text
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.py"), 'w') as file:
            file.write(database_py)
            file.close()
        cloud_conn = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/current/cloud_connection.py").text
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloud_connection.py"), 'w') as file:
            file.write(cloud_conn)
            file.close()
        with open(settings_file, 'w') as file:
            settings['version'] = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version").text
            json.dump(settings, file, indent=4)
            print("Updated settings.json")
            file.close()
        print("Updated to the latest version.")
        print("Waiting for 5 seconds before restarting...")
        sleep(5)
        print("Restarting the program...")
        t = threading.Thread(target=run_main)
        t.start()
        exit(0)
    else:
        print("You are already using the latest version.")
        exit(0)
if __name__ == "__main__":
    update()