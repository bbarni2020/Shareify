import sqlite3
import os
import requests
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder='web')

path = ""
password = ""
api_key = "ABC"
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
        with open(settings_path, 'w') as f:
            settings = requests.get(
                "https://raw.githubusercontent.com/bbarni2020/Shareify/main/host/settings/settings.json"
            ).json()
            settings['path'] = path
            json.dump(settings, f, indent=4)
    roles_path = os.path.join(os.path.dirname(__file__), 'settings/roles.json')
    if not os.path.exists(roles_path):
        with open(roles_path, 'w') as f:
            roles = requests.get(
                "https://raw.githubusercontent.com/bbarni2020/Shareify/main/host/settings/roles.json"
            ).text
            f.write(roles)

@app.route('/')
def install_page():
    return render_template('install.html')

@app.route('/set_path', methods=['POST'])
def set_path():
    global path
    path = request.form.get('path')
    if path:
        create_jsons()
        return redirect(url_for('install_page'))
    return "Path not provided", 400

@app.route('/set_password', methods=['POST'])
def set_password():
    global password
    password = request.form.get('password')
    if password:
        initialize_logs_db()
        initialize_users_db()
        return redirect(url_for('install_page'))
    return "Password not provided", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6969, debug=True)