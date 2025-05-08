import requests
import os
import json
import subprocess

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

settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
settings = load_settings(settings_file)

def update():
    if requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version").text != settings['version']:
        print("Updating...")
        try:
            requests.post("http://localhost:" + str(settings['port']) + "/update_start_exit_program", headers={"X-API-KEY": settings['api_key']})
        except:
            pass
        new_update = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/host/main.py").text
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py"), 'w') as file:
            file.write(new_update)
            print("Updated to the latest version.")
            file.close()
        with open(settings_file, 'w') as file:
            settings['version'] = requests.get("https://raw.githubusercontent.com/bbarni2020/Shareify/refs/heads/main/info/version").text
            json.dump(settings, file, indent=4)
            print("Updated settings.json")
            file.close()
        subprocess.run(["python3", os.path.join(os.path.dirname(os.path.abspath(__file__))), "main.py"])
        exit(0)
    else:
        print("You are already using the latest version.")
        exit(0)

update()