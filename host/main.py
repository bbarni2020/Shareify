#Imports
from flask import Flask, request, jsonify
import os
import json
import psutil
import sqlite3
import datetime
import mimetypes
from colorama import init, Fore, Back, Style
import subprocess
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import threading

# Initialize packages
init(autoreset=True)

class CustomAuthorizer(DummyAuthorizer):
    def edit_user(self, username, password=None, homedir=None, perm=None):
        if username not in self.user_table:
            raise ValueError(f"User '{username}' does not exist.")
        if password:
            self.user_table[username]['pwd'] = password
        if homedir:
            self.user_table[username]['home'] = homedir
        if perm:
            self.user_table[username]['perm'] = perm

authorizer = CustomAuthorizer()


def initialize_logs_db():
    db_path = os.path.join(os.path.dirname(__file__), 'logs.db')
    conn = sqlite3.connect(db_path)
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
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path)
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
            API_KEY TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'logs.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def get_users_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def start_ftp_server():
    def run_ftp():
        try:
            handler = FTPHandler
            handler.authorizer = authorizer

            handler.timeout = settings['ftp_timeout']

            address = (settings['ftp_host'], settings['ftp_port'])
            server = FTPServer(address, handler)

            print_status("FTP server started successfully.", "success")
            log("FTP server started", "-")
            server.serve_forever()
        except Exception as e:
            print_status(f"Error starting FTP server: {e}", "error")
            log("FTP server start error: " + str(e), "-")
    
    ftp_thread = threading.Thread(target=run_ftp, daemon=True)
    ftp_thread.start()

# Functions
def log(action, ip):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (timestamp, action, ip)
        VALUES (?, ?, ?)
    ''', (timestamp, action, ip))
    conn.commit()

def print_status(message, status_type="info"):
    if status_type == "success":
        print(Fore.GREEN + message)
    elif status_type == "error":
        print(Fore.RED + message)
    elif status_type == "warning":
        print(Fore.YELLOW + message)
    else:
        print(Fore.BLUE + message)

def load_settings(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                settings = json.load(file)
                return settings
            except json.JSONDecodeError:
                print("Error: Invalid JSON format in settings file.")
                log("Invalid JSON format in settings file", "-")
    else:
        print(f"Settings file '{file_path}' not found.")
        log("Settings file not found", "-")
        exit(1)

settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
settings = load_settings(settings_file)


# Flask app
app = Flask(__name__)

@app.before_request
def require_api_key():
    api_key = request.headers.get('X-API-KEY')
    if not api_key or api_key != settings.get('api_key'):
        log("Unauthorized access attempt", request.remote_addr)
        return jsonify({"error": "Unauthorized"}), 401

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    log("Shutdown", request.remote_addr)
    os.system("sudo shutdown 10")
    return jsonify({"status": "Shutting down"})

@app.route('/api/restart', methods=['POST'])
def restart():
    log("Restart", request.remote_addr)
    os.system("sudo shutdown -r 10")
    return jsonify({"status": "Restarting"})

@app.route('/api/finder', methods=['GET'])
def finder():
    try:
        path = request.args.get('path')
    except:
        path = None
    if path:
        try:
            full_path = os.path.join(settings['path'], path)
            if os.path.exists(full_path):
                items = os.listdir(full_path)
                return jsonify({"items": items})
            else:
                return jsonify({"error": "Path does not exist"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        try:
            full_path = settings['path']
            if os.path.exists(full_path):
                items = os.listdir(full_path)
                return jsonify({"items": items})
            else:
                return jsonify({"error": "Path does not exist"}), 404
        except Exception as e:
            log("Finder error: " + str(e), request.remote_addr)
            return jsonify({"error": str(e)}), 500

@app.route('/api/command', methods=['GET'])
def command():
    command = request.json.get('command')
    if command:
        try:
            stream = os.popen(command)
            output = stream.read()
            log("Command executed: " + command, request.remote_addr)
            return jsonify({"status": "Command executed", "output": output})
        except Exception as e:
            log("Command execution error: " + str(e), request.remote_addr)
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No command provided"}), 400
    
@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.json.get('folder_name')
    path = request.json.get('path')
    if folder_name:
        if path:
            try:
                full_path = os.path.join(settings['path'], path, folder_name)
                os.mkdir(full_path)
                return jsonify({"status": "Folder created", "path": path + folder_name})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            try:
                full_path = os.path.join(settings['path'], folder_name)
                os.mkdir(full_path)
                return jsonify({"status": "Folder created", "path": folder_name})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No folder name provided"}), 400
    
@app.route('/api/delete_folder', methods=['POST'])
def delete_folder():
    path = request.json.get('path')
    if path:
        try:
            full_path = os.path.join(settings['path'], path)
            if os.path.exists(full_path):
                os.rmdir(full_path)
                return jsonify({"status": "Folder deleted"})
            else:
                return jsonify ({"error": "Path does not exist"}), 404
        except Exception as e:
                return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No path provided"}), 400
    
@app.route('/api/rename_folder', methods=['POST'])
def rename_folder():
    old_name = request.json.get('folder_name')
    new_name = request.json.get('new_name')
    path = request.json.get('path')
    if old_name and new_name:
        if path:
            try:
                full_path = os.path.join(settings['path'], path, old_name)
                new_full_path = os.path.join(settings['path'], path, new_name)
                if os.path.exists(full_path):
                    os.rename(full_path, new_full_path)
                    return jsonify({"status": "Folder renamed", "path": path + new_name})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            try:
                full_path = os.path.join(settings['path'], old_name)
                new_full_path = os.path.join(settings['path'], new_name)
                if os.path.exists(full_path):
                    os.rename(full_path, new_full_path)
                    return jsonify({"status": "Folder renamed", "path": new_name})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No folder name provided"}), 400
    
@app.route('/api/resources', methods=['GET'])
def resource():
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return jsonify({"cpu": cpu, "memory": memory, "disk": disk})
    except Exception as e:
        return jsonify ({"error": str(e)}), 500
    
@app.route('/api/new_file', methods=['POST'])
def new_file():
    file_name = request.json.get('file_name')
    path = request.json.get('path')
    file_content = request.json.get('file_content')
    if file_name and file_content:
        try:
            if path:
                full_path = os.path.join(settings['path'], path, file_name)
            else:
                full_path = os.path.join(settings['path'], file_name)
            with open(full_path, 'w') as file:
                file.write(file_content)
            return jsonify({"status": "File created", "path": path + file_name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No file name or content provided"}), 400
    
@app.route('/api/delete_file', methods=['POST'])
def delete_file():
    path = request.json.get('path')
    if path:
        try:
            full_path = os.path.join(settings['path'], path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return jsonify({"status": "File deleted"})
            else:
                return jsonify({"error": "Path does not exist"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No path provided"}), 400

@app.route('/api/rename_file')
def rename_file():
    old_name = request.json.get('file_name')
    new_name = request.json.get('new_name')
    path = request.json.get('path')
    if old_name and new_name:
        if path:
            full_path = os.path.join(settings['path'], path, old_name)
            new_full_path = os.path.join(settings['path'], path, new_name)
        else:
            full_path = os.path.join(settings['path'], old_name)
            new_full_path = os.path.join(settings['path'], new_name)
        try:
            if os.path.exists(full_path):
                os.rename(full_path, new_full_path)
                return jsonify({"status": "File renamed", "path": path + new_name})
            else:
                return jsonify({"error": "Path does not exist"}), 404
        except Exception as e:
            return jsonify({"error":str(e)}), 500
    else:
        return jsonify({"error": "No file name provided"}), 400
    
@app.route('/api/get_file', methods=['GET'])
def get_file():
    file = request.json.get('file_path')
    if file:
        try:
            full_path = os.path.join(settings['path'], file)
            if os.path.exists(full_path):
                mime_type, _ = mimetypes.guess_type(full_path)
                if mime_type and (mime_type.startswith('video/') or mime_type.startswith('image/')):
                    with open(full_path, 'rb') as f:
                        content = f.read()
                    return jsonify({"status": "File content retrieved", "content": content.decode('latin1')}), 200
                else:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    return jsonify({"status": "File content retrieved", "content": content}), 200
            else:
                return jsonify({"error": "Path does not exist"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No file path provided"}), 400
    
@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs')
    logs = cursor.fetchall()
    conn.close()
    log_list = []
    for log in logs:
        log_list.append({
            "id": log[0],
            "timestamp": log[1],
            "action": log[2],
            "ip": log[3]
        })
    log("Logs retrieved", request.remote_addr)
    return jsonify(log_list)

@app.route('/api/get_settings', methods=['GET'])
def get_settings():
    try:
        with open(settings_file, 'r') as file:
            settings = json.load(file)
            return jsonify(settings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    new_settings = request.json
    if new_settings:
        try:
            with open(settings_file, 'w') as file:
                json.dump(new_settings, file)
            log("Settings updated", request.remote_addr)
            return jsonify({"status": "Settings updated"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No settings provided"}), 400

@app.route('/api/get_version', methods=['GET'])
def get_version():
    version = settings['version']
    return jsonify ({"version": version})

@app.route('/update_start_exit_program', methods=['POST'])
def update_exit():
    exit(0)

@app.route('/api/update', methods=['POST'])
def update():
    subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "update.py")])
    return jsonify({"status": "Update started"}), 200

@app.route('/api/create_ftp_user', methods=['POST'])
def create_ftp_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    path = data.get('path')
    permissions = data.get('permissions')
    if username and password and permissions:
        try:
            if path:
                full_path = os.path.join(settings['path'], path)
            else:
                full_path = settings['path']
            if not os.path.exists(full_path):
                return jsonify({"error": "Path does not exist"}), 404
            authorizer.add_user(username, password, full_path, permissions)
            log("FTP user created: " + username, request.remote_addr)
            return jsonify({"status": "FTP user created"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No username, password or permissions provided"}), 400
    
@app.route('/api/delete_ftp_user', methods=['POST'])
def delete_ftp_user():
    username = request.json.get('username')
    if username:
        try:
            authorizer.remove_user(username)
            log("FTP user deleted:" + username, request.remote_addr)
            return jsonify({"status": "FTP user deleted"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/get_ftp_users', methods=['GET'])
def get_ftp_users():
    try:
        user_list = authorizer.get_user_list()
        users = []
        for user in user_list:
            users.append({
                "username": user[0],
                "password": user[1], 
                "path": user[2],
                "permissions": user[3]
            })
        log("FPT users retrived", request.remote_addr)
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/edit_ftp_user', methods=['POST'])
def edit_ftp_user():
    username = request.json.get('username')
    password = request.json.get('password')
    path = request.json.get('path')
    permissions = request.json.get('permissions')
    if username:
        try:
            full_path = os.path.join(settings['path'], path) if path else settings['path']
            if path and not os.path.exists(full_path):
                return jsonify({"error": "Path does not exist"}), 404
            authorizer.edit_user(username, password, full_path, permissions)
            log("FTP user edited: " + username, request.remote_addr)
            return jsonify({"status": "FTP user edited"}), 200
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No username provided"}), 400

@app.route('/api/user/create', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    ip = ""
    role = data.get('role')
    ftp_user = ""
    paths = data.get('paths')
    settings = ""
    if username and password and name and role:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, name, ip, role, ftp_user, paths, settings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?))
                           ''', (username, password, name, ip, role, ftp_user, paths, settings))
            conn.commit()
            conn.close()
            log("User created: " + username, request.remote_addr)
            return jsonify({"status": "User created"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No username, password, name or role provided"}), 400

@app.route('/api/user/delete', mothods=['POST'])
def delete_user():
    username = request.json.get('username')
    if username:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                           DELETE FROM users WHERE username = ?
                           ''', (username))
            conn.commit()
            conn.close()
            log("User deleted: " + username, request.remote_addr)
            return jsonify({"status": "User deleted"}), 200
        except Exception as e:
            return jsonify ({"error": str(e)}), 500
        else:
            return jsonify({"error": "No username provided"}), 400
    
@app.route('/api/user/edit', methods=['GET'])
def edit_user():
    username = request.json.get('username')
    password = request.json.get('password')
    name = request.json.get('name')
    role = request.json.get('role')
    paths = request.json.get('paths')
    id = request.json.get('id')
    if username and password and name and role and paths and id:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE users
                           SET username = ?, password = ?, name = ?, role = ?, paths = ?
                           WHERE id = ?
                           '''), (username, password, name, role, paths, id)
            log("User edited: " + username, request.remote_addr)
            conn.commit()
            conn.close()
            return jsonify({"status": "User edited"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No username, password, name, role or paths provided"}), 400

@app.route('/api/user/login', methods=['GET'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username and password:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                           SELECT * FROM users WHERE username = ? AND password = ?
                           ''', (username, password))
            user = cursor.fetchone()
            conn.close()
            if user:
                log("User logged in: " + username, request.remote_addr)
                return jsonify({"API_KEY": user[9]}), 200
            else:
                log("Invalid login attempt: " + username, request.remote_addr)
                return jsonify({"error": "Invalid username or password"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No username or password provided"}), 400
    

# Main
print(r"""
 __ _                     __       
/ _\ |__   __ _ _ __ ___ / _|_   _ 
\ \| '_ \ / _` | '__/ _ \ |_| | | |
_\ \ | | | (_| | | |  __/  _| |_| |
\__/_| |_|\__,_|_|  \___|_|  \__, |
                             |___/ 
""")


if settings:
    print_status("Settings loaded successfully.", "success")
    initialize_logs_db()
    initialize_users_db()
    try:
        start_ftp_server()
        app.run(host=settings['host'], port=settings['port'], debug=False)
    except Exception as e:
        print_status(f"Error starting server: {e}", "error")
        log("Server start error: " + str(e), "-")
        exit(1)
else:
    print_status("Failed to load settings. Exiting.", "error")
    print_status("Please check the documentation for more.", "info")
    exit(1)