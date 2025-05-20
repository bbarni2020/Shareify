import requests
import os
import json
import sqlite3
import threading

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
        print("Updating...")
        try:
            api_key = get_admin_api_key()
            requests.post(
                "http://localhost:" + str(settings['port']) + "/update_start_exit_program",
                headers={"X-API-KEY": api_key}
            )
        except:
            print("Error: Unable to send update_start_exit_program request. Make sure the server is running.")
            pass
        new_update = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/host/main.py").text
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"), 'w') as file:
            file.write(new_update)
            print("Updated to the latest version.")
            file.close()
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
        index_html = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/host/web/index.html").text
        with open(os.path.join(web_dir, "index.html"), 'w') as file:
            file.write(index_html)
        install_html = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/host/web/install.html").text
        with open(os.path.join(web_dir, "install.html"), 'w') as file:
            file.write(install_html)
        index_css = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/host/web/index.css").text
        with open(os.path.join(web_dir, "index.css"), 'w') as file:
            file.write(index_css)
        database_py = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/host/database.py").text
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.py"), 'w') as file:
            file.write(database_py)
        with open(settings_file, 'w') as file:
            settings['version'] = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version").text
            json.dump(settings, file, indent=4)
            print("Updated settings.json")
            file.close()
        t = threading.Thread(target=run_main)
        t.start()
        exit(0)
    else:
        print("You are already using the latest version.")
        exit(0)

update()