#Imports
from flask import Flask, request, jsonify, g, send_from_directory
import os
import json
import psutil
import sqlite3
import datetime
import mimetypes
from colorama import init, Fore, Back, Style
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import threading
from flask_cors import CORS
import secrets
from time import sleep
import threading
import sys
import ctypes
import update
from werkzeug.utils import secure_filename
import zipfile
import tempfile
import shutil

def is_admin():
    try:
        if os.name == 'nt':
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def relaunch_as_admin():
    if os.name == 'nt':
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    else:
        os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
    sys.exit(0)

if not is_admin():
    print("main.py is not running as administrator/root. Trying to relaunch as admin/root...")
    #relaunch_as_admin()

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
    
    def get_user_list(self):
        """Return a list of all FTP users with their details."""
        user_list = []
        for username, user_data in self.user_table.items():
            user_list.append([
                username,
                user_data.get('pwd', ''),
                user_data.get('home', ''),
                user_data.get('perm', '')
            ])
        return user_list

authorizer = CustomAuthorizer()
logs_db_path = os.path.join(os.path.dirname(__file__), 'db/logs.db')
users_db_path = os.path.join(os.path.dirname(__file__), 'db/users.db')

ftp_server_instance = None

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
    db_path = os.path.join(os.path.dirname(__file__), 'db/users.db')
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
            API_KEY TEXT NOT NULL,
            paths_write TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(logs_db_path, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def get_users_db_connection():
    conn = sqlite3.connect(users_db_path, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def start_ftp_server():
    global ftp_server_instance
    def run_ftp():
        try:
            handler = FTPHandler
            handler.authorizer = authorizer

            handler.timeout = settings['ftp_timeout']

            address = (settings['ftp_host'], settings['ftp_port'])
            ftp_server_instance = FTPServer(address, handler)

            print_status("FTP server started successfully.", "success")
            log("FTP server started", "-")
            ftp_server_instance.serve_forever()
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
                print_status("Error: Invalid JSON format in settings file.", "error")
                log("Invalid JSON format in settings file", "-")
    else:
        print_status(f"Settings file '{file_path}' not found.", "error")
        log("Settings file not found", "-")
        exit(1)

def load_roles(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                roles = json.load(file)
                return roles
            except json.JSONDecodeError:
                print_status("Error: Invalid JSON format in roles file.", "error")
    else:
        print_status("Roles file not found.", "error")
        log("Roles file not found", "-")
        exit(1)

def generate_unique_api_key():
    conn = get_users_db_connection()
    cursor = conn.cursor()
    while True:
        api_key = secrets.token_hex(32)
        cursor.execute('SELECT 1 FROM users WHERE API_KEY = ?', (api_key,))
        if not cursor.fetchone():
            conn.close()
            return api_key

def stop_completely():
    global ftp_server_instance
    print_status("Initiating server shutdown...", "info")
    log("Initiating server shutdown", "-")
    
    if ftp_server_instance:
        try:
            print_status("Stopping FTP server...", "info")
            ftp_server_instance.close_all()
            ftp_server_instance = None
            print_status("FTP server stopped", "success")
        except Exception as e:
            print_status(f"Error stopping FTP server: {e}", "error")

    try:
        def shutdown_server():
            sleep(1)
            print_status("Server shutdown complete", "success")
            update.kill_process_on_port(settings['port'])
            os._exit(0)
        return True
    except Exception as e:
        print_status(f"Error during shutdown: {e}", "error")
        log(f"Error during shutdown: {e}", "-")
        os._exit(1)
    
settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings/settings.json")
roles_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings/roles.json")
settings = load_settings(settings_file)
roles = load_roles(roles_file)
def reload_jsons():
    settings = load_settings(settings_file)
    roles = load_roles(roles_file)

def is_accessible(address):
    try:
        list = roles.get('/api/role/get', [])
        for item in list:
            if item == g.role:
                return True
        log("Unauthorized access attempt", request.remote_addr)
        return False
    except Exception as e:
        print_status("Error: " + str(e), "error")
        log("Error on is_accessible: " + str(e), "-")
        return False

def has_access(path):
    result = g.result
    if result:
        paths = result[7]
        if paths:
            paths = json.loads(paths)
            for p in paths:
                if path.startswith(p):
                    return True
    return False

def has_write_access(path):
    result = g.result
    if result:
        paths_write = result[10]
        if paths_write:
            paths_write = json.loads(paths_write)
            for p in paths_write:
                if path.startswith(p):
                    return True
    return False

# Flask app
app = Flask(__name__)
CORS(app)

@app.before_request
def require_api_key():
    if request.endpoint in ['login', 'is_up', 'root', 'serve_static', 'serve_assets', 'auth']:
        return
    api_key = request.headers.get('X-API-KEY')
    conn = get_users_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users WHERE API_KEY = ?
    ''', (api_key,))
    result = cursor.fetchone()
    conn.close()
    if not result or not api_key:
        log("Unauthorized access attempt", request.remote_addr)
        return jsonify({"error": "Unauthorized"}), 401
    else:
        role = result[5]
        g.role = role
        g.result = result
        if not is_accessible(request.path):
            return jsonify({"error": "Unauthorized"}), 401

@app.after_request
def update_ip(response):
    if response.status_code == 200:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users
                SET ip = ?
                WHERE API_KEY = ?
            ''', (request.remote_addr, request.headers.get('X-API-KEY')))
            conn.commit()
            conn.close()
        except Exception as e:
            print_status(f"Error updating IP in database: {e}", "error")
    return response

@app.route('/api/is_up', methods=['GET'])
def is_up():
    return jsonify({"status": "Server is up"}), 200

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    log("Shutdown", request.remote_addr)
    if os.name == 'nt':
        os.system("shutdown /s /t 10")
    else:
        os.system("sudo shutdown -h +1")
    return jsonify({"status": "Shutting down"})

@app.route('/api/restart', methods=['POST'])
def restart():
    log("Restart", request.remote_addr)
    if os.name == 'nt':
        os.system("shutdown /r /t 10")
    else:
        os.system("sudo shutdown -r +1")
    return jsonify({"status": "Restarting"})

@app.route('/api/finder', methods=['GET'])
def finder():
    try:
        path = request.args.get('path')
    except:
        path = None
    if path:
        try:
            if has_access(path):
                full_path = os.path.join(settings['path'], path)
                if os.path.exists(full_path):
                    items = os.listdir(full_path)
                    return jsonify({"items": items})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            else:
                log("Unauthorized access attempt", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        try:
            if has_access(""):
                full_path = settings['path']
                if os.path.exists(full_path):
                    items = os.listdir(full_path)
                    return jsonify({"items": items})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            else:
                log("Unauthorized access attempt", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
        except Exception as e:
            log("Finder error: " + str(e), request.remote_addr)
            return jsonify({"error": str(e)}), 500

current_command_dir = None

def get_command_dir():
    global current_command_dir
    if current_command_dir is None:
        current_command_dir = settings['path']
    return current_command_dir

def set_command_dir(new_dir):
    global current_command_dir
    current_command_dir = new_dir

@app.route('/api/command', methods=['POST'])
def command():
    command = request.json.get('command')
    if command:
        try:
            command = command.strip()
            
            if command.startswith('cd '):
                target_dir = command[3:].strip()
                if target_dir == '~' or target_dir == '':
                    new_dir = settings['path']
                elif target_dir.startswith('/'):
                    new_dir = target_dir
                elif target_dir == '..':
                    current_dir = get_command_dir()
                    new_dir = os.path.dirname(current_dir)
                else:
                    current_dir = get_command_dir()
                    new_dir = os.path.join(current_dir, target_dir)
                
                new_dir = os.path.abspath(new_dir)
                
                if os.path.exists(new_dir) and os.path.isdir(new_dir):
                    set_command_dir(new_dir)
                    log("Command executed: " + command, request.remote_addr)
                    return jsonify({"status": "Command executed", "output": f"Changed directory to: {target_dir}"})
                else:
                    return jsonify({"status": "Command executed", "output": f"cd: {target_dir}: No such file or directory"})
            
            elif command == 'pwd':
                current_dir = get_command_dir()
                log("Command executed: " + command, request.remote_addr)
                return jsonify({"status": "Command executed", "output": current_dir})
            
            else:
                current_dir = get_command_dir()
                if os.name == 'nt':
                    full_command = f'cd /d "{current_dir}" && {command}'
                else:
                    full_command = f'cd "{current_dir}" && {command}'
                
                stream = os.popen(full_command)
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
            if has_write_access(path):
                try:
                    full_path = os.path.join(settings['path'], path, folder_name)
                    os.mkdir(full_path)
                    return jsonify({"status": "Folder created", "path": path + folder_name})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
            else:
                log("Unauthorized access attempt", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
        else:
            if has_write_access(""):
                try:
                    full_path = os.path.join(settings['path'], folder_name)
                    os.mkdir(full_path)
                    return jsonify({"status": "Folder created", "path": folder_name})
                except Exception as e:
                    return jsonify({"error": str(e)}), 500
            else:
                log("Unauthorized access attempt", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No folder name provided"}), 400
    
@app.route('/api/delete_folder', methods=['POST'])
def delete_folder():
    path = request.json.get('path')
    if path:
        if has_write_access(path):
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
            log("Unauthorized access attempt", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No path provided"}), 400
    
@app.route('/api/rename_folder', methods=['POST'])
def rename_folder():
    old_name = request.json.get('folder_name')
    new_name = request.json.get('new_name')
    path = request.json.get('path')
    if old_name and new_name:
        if path:
            if has_write_access(path):
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
                log("Unauthorized access attempt", request.remote_addr)
        else:
            if has_write_access(""):
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
                log("Unauthorized access attempt", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No folder name provided"}), 400
    
@app.route('/api/resources', methods=['GET'])
def resource():
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return jsonify({"cpu": int(cpu), "memory": int(memory), "disk": int(disk)})
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
        if has_write_access(path):
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
            log("Unauthorized access attempt", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
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
            return jsonify({"error": "No path provided"}), 400
        if has_write_access(path):
            try:
                if os.path.exists(full_path):
                    os.rename(full_path, new_full_path)
                    return jsonify({"status": "File renamed", "path": path + new_name})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            except Exception as e:
                return jsonify({"error":str(e)}), 500
        else:
            log("Unauthorized access attempt", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No file name provided"}), 400
    
@app.route('/api/get_file', methods=['GET'])
def get_file():
    file = request.json.get('file_path')
    if file:
        if has_write_access(file):
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
            log("Unauthorized access attempt", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No file path provided"}), 400
    
@app.route('/api/edit_file', methods=['POST'])
def edit_file():
    path = request.json.get('path')
    file_content = request.json.get('file_content')
    if not file_content:
        file_content = ""
    if path:
        if has_write_access(path):
            try:
                full_path = os.path.join(settings['path'], path)
                with open(full_path, 'w') as file:
                    file.write(file_content)
                    file.close()
                return jsonify({"status": "File edited", "path": path})
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            log("Unauthorized acces attempt", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No path provided"}), 400
    
@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY id DESC')
    logs = cursor.fetchall()
    conn.close()
    log_list = []
    for loger in logs:
        log_list.append({
            "id": loger[0],
            "timestamp": loger[1],
            "action": loger[2],
            "ip": loger[3]
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
                file.close
            log("Settings updated", request.remote_addr)
            reload_jsons()
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
    stop_completely()
    return jsonify({"status": "Update started"}), 200

@app.route('/api/update', methods=['POST'])
def update_server():
    def run_update():
        print_status("Update started", "info")
        os.system(f'python3 "{os.path.join(os.path.dirname(__file__), "update.py")}"')
    t = threading.Thread(target=run_update)
    t.start()
    return jsonify({"status": "Update started"}), 200

@app.route('/api/ftp/create_user', methods=['POST'])
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
    
@app.route('/api/ftp/delete_user', methods=['POST'])
def delete_ftp_user():
    username = request.json.get('username')
    if username:
        try:
            authorizer.remove_user(username)
            log("FTP user deleted:" + username, request.remote_addr)
            return jsonify({"status": "FTP user deleted"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/ftp/get_users', methods=['GET'])
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
        print("Error retrieving FTP users:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/ftp/edit_user', methods=['POST'])
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

@app.route('/api/ftp/start', methods=['POST'])
def start_ftp_server_from_api():
    try:
        start_ftp_server()
        log("FTP server started from API", request.remote_addr)
        new_settings = settings.copy()
        new_settings['ftp'] = True
        with open(settings_file, 'w') as file:
                json.dump(new_settings, file)
        print_status("FTP server started from API", "success")
        return jsonify({"status": "FTP server started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/ftp/stop', methods=['POST'])
def stop_ftp_server_from_api():
    global ftp_server_instance
    if ftp_server_instance:
        try:
            ftp_server_instance.close_all()
            ftp_server_instance = None
            log("FTP server stopped from API", request.remote_addr)
            print_status("FTP server stopped from API", "success")
            return jsonify({"status": "FTP server stopped"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "FTP server is not running"}), 400

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
    settings_val = ""
    paths_write = data.get('paths_write', "")
    if username and password and name and role:
        try:
            api_key = generate_unique_api_key()
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, name, ip, role, ftp_users, paths, settings, API_KEY, paths_write)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, password, name, ip, role, ftp_user, paths, settings_val, api_key, paths_write))
            conn.commit()
            conn.close()
            log("User created: " + username, request.remote_addr)
            return jsonify({"status": "User created", "API_KEY": api_key}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No username, password, name or role provided"}), 400

@app.route('/api/user/delete', methods=['POST'])
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
    paths_write = request.json.get('paths_write')
    id = request.json.get('id')
    if username and password and name and role and paths and id:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                           UPDATE users
                           SET username = ?, password = ?, name = ?, role = ?, paths = ?, paths_write = ?
                           WHERE id = ?
                           '''), (username, password, name, role, paths, paths_write,id)
            log("User edited: " + username, request.remote_addr)
            conn.commit()
            conn.close()
            return jsonify({"status": "User edited"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "No username, password, name, role or paths provided"}), 400

@app.route('/api/user/login', methods=['POST'])
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

@app.route('/api/user/get_self', methods=['GET'])
def get_user():
    data = g.result
    if data:
        user = {
            "username": data[1],
            "password": data[2],
            "name": data[3],
            "role": data[5],
            "ftp_users": data[6],
            "paths": data[7],
            "settings": data[8],
            "paths_write": data[10]
        }
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404
    
@app.route('/api/user/get_all', methods=['GET'])
def get_all_users():
    try:
        conn = get_users_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        conn.close()
        user_list = []
        for user in users:
            user_list.append({
                "username": user[1],
                "password": user[2],
                "name": user[3],
                "ip": user[4],
                "role": user[5],
                "ftp_users": user[6],
                "paths": user[7],
                "settings": user[8],
                "API_KEY": user[9],
                "paths_write": user[10]
            })
        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/user/edit_self', methods=['POST'])
def self_edit_user():
    data = g.result
    username = request.json.get('username')
    password = request.json.get('password')
    name = request.json.get('name')
    ftp_users = request.json.get('ftp_users')
    settings = request.json.get("settings")
    key = request.json.get("API_KEY")
    
    if data:
        conn = get_users_db_connection()
        cursor = conn.cursor()
        updates = []
        params = []

        if username:
            updates.append("username = ?")
            params.append(username)
        if password:
            updates.append("password = ?")
            params.append(password)
        if name:
            updates.append("name = ?")
            params.append(name)
        if ftp_users:
            updates.append("ftp_users = ?")
            params.append(ftp_users)
        if settings:
            updates.append("settings = ?")
            params.append(settings)
        if key:
            updates.append("API_KEY = ?")
            params.append(key)

        if updates:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            params.append(data[0])
            try:
                cursor.execute(query, tuple(params))
                conn.commit()
                log("User self-edited: " + data[1], request.remote_addr)
                return jsonify({"status": "User updated"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            finally:
                conn.close()
        else:
            return jsonify({"error": "No valid fields provided for update"}), 400
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/api/role/get', methods=['GET'])
def get_roles():
    try:
        with open(roles_file, 'r') as file:
            roles = json.load(file)
            return jsonify(roles)
    except Exception as e:
        return jsonify ({"error": str(e)}), 500

@app.route('/api/role/edit', methods=['POST'])
def edit_roles():
    new_roles = request.json
    if new_roles:
        try:
            with open(roles_file, 'w') as file:
                json.dump(new_roles, file)
                file.close()
            log('Roles updated', request.remote_addr)
            reload_jsons()
            return jsonify ({"status": "Roles update"}), 200
        except Exception as e:
            return jsonify ({"error": str(e)}), 500
    else:
        return jsonify ({"error": "No roles provided"}), 400

@app.route('/', methods=['GET'])
def root():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), 'index.html')

@app.route('/auth', methods=['GET'])
def auth():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), 'login.html')

@app.route('/web/<path:filename>', methods=['GET'])
def serve_static(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), filename)

@app.route('/web/assets/<path:filename>', methods=['GET'])
def serve_assets(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web', 'assets'), filename, mimetype=mimetypes.guess_type(filename)[0])

@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    path = request.form.get('path', '')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    if path is None:
        path = ''
    if not has_write_access(path):
        return jsonify({"error": "Unauthorized"}), 401
    filename = secure_filename(file.filename)
    dest_dir = os.path.join(settings['path'], path) if path else settings['path']
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    try:
        file.save(dest_path)
        log(f"File uploaded", request.remote_addr)
        return jsonify({"status": "File uploaded"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/download', methods=['GET'])
def download_file():
    file_path = request.args.get('file_path')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
    if not has_access(file_path):
        return jsonify({"error": "Unauthorized"}), 401
    full_path = os.path.join(settings['path'], file_path)
    if os.path.exists(full_path):
        if os.path.isfile(full_path):
            directory = os.path.dirname(full_path)
            filename = os.path.basename(full_path)
            return send_from_directory(directory, filename, as_attachment=True)
        elif os.path.isdir(full_path):  
            temp_dir = tempfile.mkdtemp()
            zip_filename = f"{os.path.basename(file_path)}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)
            
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(full_path):
                        for file in files:
                            file_full_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_full_path, full_path)
                            zipf.write(file_full_path, arcname)                
                def cleanup_temp_file():
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                
                response = send_from_directory(temp_dir, zip_filename, as_attachment=True)
                response.call_on_close(cleanup_temp_file)
                return response
                
            except Exception as e:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return jsonify({"error": f"Failed to create zip: {str(e)}"}), 500
    
    return jsonify({"error": "File or folder does not exist"}), 404

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
        update.kill_process_on_port(settings['port'])
        if settings['ftp']:
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