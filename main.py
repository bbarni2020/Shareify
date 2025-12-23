#Imports
from flask import Flask, request, jsonify, g, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
import jwt
import requests
import base64
import hashlib
import re
try:
    from argon2 import PasswordHasher
except Exception:
    PasswordHasher = None

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

try:
    import bcrypt
except Exception:
    bcrypt = None
ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2, hash_len=32) if PasswordHasher else None

def hash_password(p):
    if bcrypt:
        try:
            return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except Exception:
            pass
    if ph:
        try:
            return ph.hash(p)
        except Exception:
            pass
    return p

def verify_password(stored, p):
    if stored and (stored.startswith('$2b$') or stored.startswith('$2y$')) and bcrypt:
        try:
            return bcrypt.checkpw(p.encode('utf-8'), stored.encode('utf-8'))
        except Exception:
            return False
    if stored and stored.startswith('$argon2') and ph:
        try:
            return ph.verify(stored, p)
        except Exception:
            return False
    return stored == p

def needs_rehash(stored):
    return not (stored and (stored.startswith('$2b$') or stored.startswith('$2y$') or stored.startswith('$argon2')))


class HashedAuthorizer(CustomAuthorizer):
    def add_user(self, username, password, homedir, perm=None):
        pwd_hash = password if not needs_rehash(password) else hash_password(password)

        super().add_user(username, password, homedir, perm)
        if username in self.user_table:
            self.user_table[username]['pwd_hash'] = pwd_hash
            self.user_table[username]['pwd'] = ''

    def validate_authentication(self, username, password, handler):
        user = self.user_table.get(username)
        if not user:
            return False
        stored_hash = user.get('pwd_hash') or user.get('pwd')
        if not stored_hash:
            return False
        return verify_password(stored_hash, password)


authorizer = HashedAuthorizer()
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
            paths_write TEXT,
            must_change INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ftp_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            homedir TEXT NOT NULL,
            permissions TEXT NOT NULL
        )
    ''')
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN must_change INTEGER DEFAULT 0')
    except Exception:
        pass
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

def flag_weak_passwords():
    try:
        conn = get_users_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password FROM users')
        rows = cursor.fetchall()
        for uid, uname, pwd in rows:
            weak = False
            if needs_rehash(pwd):
                weak = True
            if pwd == uname or (pwd and pwd.lower() in ['admin','password','123456']):
                weak = True
            if weak:
                try:
                    cursor.execute('UPDATE users SET must_change = 1 WHERE id = ?', (uid,))
                except Exception:
                    pass
        conn.commit()
        conn.close()
    except Exception:
        pass

def save_ftp_user_to_db(username, password, homedir, permissions):
    conn = get_users_db_connection()
    cursor = conn.cursor()
    pwd_to_store = password if not needs_rehash(password) else hash_password(password)

    cursor.execute('''
        INSERT OR REPLACE INTO ftp_users (username, password, homedir, permissions)
        VALUES (?, ?, ?, ?)
    ''', (username, pwd_to_store, homedir, permissions))
    conn.commit()
    conn.close()

def delete_ftp_user_from_db(username):
    conn = get_users_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ftp_users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def load_ftp_users_from_db():
    conn = get_users_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, password, homedir, permissions FROM ftp_users')
    ftp_users = cursor.fetchall()
    conn.close()
    
    for username, password, homedir, permissions in ftp_users:
        try:
            authorizer.add_user(username, password, homedir, permissions)
            print_status(f"Loaded FTP user: {username}", "success")
        except Exception as e:
            print_status(f"Error loading FTP user {username}: {e}", "error")

def start_ftp_server():
    global ftp_server_instance, settings
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
        raw = secrets.token_hex(32)
        api_key = hashlib.sha256((raw + os.environ.get('APP_SECRET','')).encode()).hexdigest()
        cursor.execute('SELECT 1 FROM users WHERE API_KEY = ?', (api_key,))
        if not cursor.fetchone():
            conn.close()
            return api_key

def stop_completely():
    global ftp_server_instance, settings
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
    global settings, roles
    settings = load_settings(settings_file)
    roles = load_roles(roles_file)

def _root_base():
    try:
        return os.path.realpath(settings['path'])
    except Exception:
        return os.path.realpath('/')

def _within(p):
    try:
        return os.path.realpath(p).startswith(_root_base())
    except Exception:
        return False

def is_accessible(address):
    try:
        global roles
        list = roles.get(address, [])
        for item in list:
            if item == g.role:
                return True
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

def is_cloud_on():
    try:
        cloud_path = os.path.join(os.path.dirname(__file__), 'settings', 'cloud.json')
        if os.path.exists(cloud_path):
            with open(cloud_path, 'r') as f:
                settings = json.load(f)
                if settings.get('enabled', '') == 'true':
                    return True
                else:
                    return False
    except Exception as e:
        print(f"Error reading cloud settings: {e}")
    return None

# Flask app
app = Flask(__name__)
allowed_origins_env = os.environ.get('ALLOWED_ORIGINS', '')
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(',') if o.strip()]
else:
    lan_patterns = [
        re.compile(r'^https?://10\.(?:\d{1,3}\.){2}\d{1,3}(?::\d+)?$'),
        re.compile(r'^https?://192\.168\.(?:\d{1,3})\.(?:\d{1,3})(?::\d+)?$'),
        re.compile(r'^https?://172\.(?:1[6-9]|2\d|3[0-1])\.(?:\d{1,3})\.(?:\d{1,3})(?::\d+)?$'),
        re.compile(r'^https?://localhost(?::\d+)?$'),
        re.compile(r'^https?://127\.0\.0\.1(?::\d+)?$'),
        re.compile(r'^https?://.*\.local(?::\d+)?$')
    ]
    origins = ['https://bridge.bbarni.hackclub.app'] + lan_patterns
CORS(app, resources={r"/*": {"origins": origins, "supports_credentials": True}})
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)

limiter = Limiter(
    app,
    default_limits=[]
)

@app.before_request
def require_jwt():
    if request.endpoint in ['login', 'is_up', 'root', 'serve_static', 'serve_assets', 'auth', 'preview']:
        return
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        log(str("Unauthorized access attempt (JWT not found) " + (request.endpoint or "")), request.remote_addr)
        return jsonify({"error": "Unauthorized"}), 401
    
    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        conn = get_users_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            log(str("Unauthorized access attempt (user not found) " + (request.endpoint or "")), request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
        
        role = result[5]
        g.role = role
        g.result = result
        g.user_id = user_id
        g.must_change = (len(result) > 11 and result[11] == 1)
        if request.endpoint in ['get_user', 'self_edit_user', 'get_self_role', 'change_password']:
            return
        if g.must_change:
            return jsonify({"error": "Password change required"}), 403
        if not is_accessible(request.path):
            return jsonify({"error": "Unauthorized"}), 401
    except jwt.ExpiredSignatureError:
        log(str("Unauthorized access attempt (JWT expired) " + (request.endpoint or "")), request.remote_addr)
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        log(str("Unauthorized access attempt (JWT invalid) " + (request.endpoint or "")), request.remote_addr)
        return jsonify({"error": "Invalid token"}), 401

@app.after_request
def update_ip(response):
    if response.status_code == 200 and hasattr(g, 'user_id'):
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            if (not is_cloud_on()) or request.remote_addr != '127.0.0.1':
                cursor.execute('''
                    UPDATE users
                    SET ip = ?
                    WHERE id = ?
                ''', (request.remote_addr, g.user_id))
                conn.commit()
                conn.close()
        except Exception as e:
            print_status(f"Error updating IP in database: {e}", "error")
    try:
        response.headers['X-Content-Type-Options'] = 'nosniff'
        csp = (
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://raw.githubusercontent.com; "
            "worker-src 'self' blob:; "
            "object-src 'none'; "
            "frame-ancestors 'none'"
        )
        response.headers['Content-Security-Policy'] = csp
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), accelerometer=(), gyroscope=(), '
            'payment=(), usb=(), xr-spatial-tracking=(), browsing-topics=()'
        )
        if os.environ.get('ENABLE_HSTS','false').lower()=='true':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    except Exception:
        pass
    return response

@app.route('/api/is_up', methods=['GET'])
@limiter.limit("1/second", override_defaults=False)
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
        os.system("sudo reboot")
    return jsonify({"status": "Restarting"})

@app.route('/api/finder', methods=['GET'])
def finder():
    global settings
    try:
        path = request.args.get('path')
    except:
        path = None
    if path:
        try:
            if has_access(path):
                full_path = os.path.normpath(os.path.join(settings['path'], path))
                if not _within(full_path):
                    return jsonify({"error": "Unauthorized"}), 401
                if os.path.exists(full_path):
                    items = os.listdir(full_path)
                    return jsonify({"items": items})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            else:
                log("Unauthorized access attempt in finder", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    else:
        try:
            if has_access(""):
                full_path = os.path.normpath(settings['path'])
                if not _within(full_path):
                    return jsonify({"error": "Unauthorized"}), 401
                if os.path.exists(full_path):
                    items = os.listdir(full_path)
                    return jsonify({"items": items})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            else:
                log("Unauthorized access attempt in finder", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
        except Exception as e:
            log("Finder error: " + str(e), request.remote_addr)
            return jsonify({"error": "Internal server error"}), 500

current_command_dir = None

def get_command_dir():
    global current_command_dir, settings
    if current_command_dir is None:
        current_command_dir = settings['path']
    return current_command_dir

def set_command_dir(new_dir):
    global current_command_dir
    current_command_dir = new_dir

@app.route('/api/command', methods=['POST'])
@limiter.limit("10/minute", override_defaults=False)
def command():
    global settings
    command = request.json.get('command')
    if command:
        try:
            command = command.strip()
            if command.startswith('mkdir '):
                target_dir = command[6:].strip()
                if target_dir == '' or target_dir == '~':
                    new_dir = settings['path']
                elif target_dir.startswith('/'):
                    new_dir = target_dir
                elif target_dir == '..':
                    current_dir = get_command_dir()
                    new_dir = os.path.dirname(current_dir)
                else:
                    current_dir = get_command_dir()
                    new_dir = os.path.normpath(os.path.join(current_dir, target_dir))
                new_dir = os.path.normpath(os.path.abspath(new_dir))
                if has_write_access(new_dir):
                    if not new_dir.startswith(settings['path']):
                        return jsonify({"error": "Unauthorized"}), 401
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                        return jsonify({"status": "Command executed", "output": f"Created directory: {target_dir}"})
                else:
                    log("Unauthorized access attempt in creating directory", request.remote_addr)
                    return jsonify({"error": "Unauthorized"}), 401
            if command.startswith('nano'):
                return jsonify({"status": "Command executed", "output": "Nano editor is not supported."})
            if command.startswith('cd '):
                target_dir = command[3:].strip()
                if target_dir == '~' or target_dir == '.' or target_dir == '':
                    new_dir = settings['path']
                elif target_dir.startswith('/'):
                    new_dir = target_dir
                elif target_dir == '..':
                    current_dir = get_command_dir()
                    new_dir = os.path.dirname(current_dir)
                else:
                    current_dir = get_command_dir()
                    new_dir = os.path.normpath(os.path.join(current_dir, target_dir))
                
                new_dir = os.path.normpath(os.path.abspath(new_dir))
                
                if not _within(new_dir):
                    return jsonify({"status": "Command executed", "output": f"cd: {target_dir}: Permission denied"})
                
                if os.path.exists(new_dir) and os.path.isdir(new_dir):
                    set_command_dir(new_dir)
                    return jsonify({"status": "Command executed", "output": f"Changed directory to: {target_dir}"})
                else:
                    return jsonify({"status": "Command executed", "output": f"cd: {target_dir}: No such file or directory"})
            
            elif command == 'pwd':
                current_dir = get_command_dir()
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
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No command provided"}), 400
    
@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    global settings
    folder_name = request.json.get('folder_name')
    path = request.json.get('path')
    if folder_name:
        if path:
            if has_write_access(path):
                try:
                    full_path = os.path.normpath(os.path.join(settings['path'], path, folder_name))
                    if not _within(full_path):
                        return jsonify({"error": "Unauthorized"}), 401
                    os.mkdir(full_path)
                    return jsonify({"status": "Folder created", "path": path + folder_name})
                except Exception as e:
                    return jsonify({"error": "Internal server error"}), 500
            else:
                log("Unauthorized access attempt in creating folder", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
        else:
            if has_write_access(""):
                try:
                    full_path = os.path.normpath(os.path.join(settings['path'], folder_name))
                    if not _within(full_path):
                        return jsonify({"error": "Unauthorized"}), 401
                    os.mkdir(full_path)
                    return jsonify({"status": "Folder created", "path": folder_name})
                except Exception as e:
                    return jsonify({"error": "Internal server error"}), 500
            else:
                log("Unauthorized access attempt in creating folder", request.remote_addr)
                return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No folder name provided"}), 400
    
@app.route('/api/delete_folder', methods=['POST'])
def delete_folder():
    global settings
    path = request.json.get('path')
    if path:
        if has_write_access(path):
            try:
                full_path = os.path.normpath(os.path.join(settings['path'], path))
                if not _within(full_path):
                    return jsonify({"error": "Unauthorized"}), 401
                if os.path.exists(full_path):
                    shutil.rmtree(full_path)
                    return jsonify({"status": "Folder deleted"})
                else:
                    return jsonify ({"error": "Path does not exist"}), 404
            except Exception as e:
                    return jsonify({"error": "Internal server error"}), 500
        else:
            log("Unauthorized access attempt in deleting folder", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No path provided"}), 400
    
@app.route('/api/rename_folder', methods=['POST'])
def rename_folder():
    global settings
    old_name = request.json.get('folder_name')
    new_name = request.json.get('new_name')
    path = request.json.get('path')
    if old_name and new_name:
        if path:
            if has_write_access(path):
                try:
                    full_path = os.path.normpath(os.path.join(settings['path'], path, old_name))
                    new_full_path = os.path.normpath(os.path.join(settings['path'], path, new_name))
                    if not _within(full_path) or not _within(new_full_path):
                        return jsonify({"error": "Unauthorized"}), 401
                    if os.path.exists(full_path):
                        os.rename(full_path, new_full_path)
                        return jsonify({"status": "Folder renamed", "path": path + new_name})
                    else:
                        return jsonify({"error": "Path does not exist"}), 404
                except Exception as e:
                    return jsonify({"error": "Internal server error"}), 500
            else:
                log("Unauthorized access attempt in renameing folder", request.remote_addr)
        else:
            if has_write_access(""):
                try:
                    full_path = os.path.normpath(os.path.join(settings['path'], old_name))
                    new_full_path = os.path.normpath(os.path.join(settings['path'], new_name))
                    if not _within(full_path) or not _within(new_full_path):
                        return jsonify({"error": "Unauthorized"}), 401
                    if os.path.exists(full_path):
                        os.rename(full_path, new_full_path)
                        return jsonify({"status": "Folder renamed", "path": new_name})
                    else:
                        return jsonify({"error": "Path does not exist"}), 404
                except Exception as e:
                    return jsonify({"error": "Internal server error"}), 500
            else:
                log("Unauthorized access attempt in renameing folder", request.remote_addr)
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
        return jsonify ({"error": "Internal server error"}), 500

    
@app.route('/api/new_file', methods=['POST'])
def new_file():
    global settings
    file_name = request.json.get('file_name')
    path = request.json.get('path')
    file_content = request.json.get('file_content')
    if file_name and file_content:
        try:
            if path:
                full_path = os.path.normpath(os.path.join(settings['path'], path, file_name))
            else:
                full_path = os.path.normpath(os.path.join(settings['path'], file_name))
            if not _within(full_path):
                return jsonify({"error": "Unauthorized"}), 401
            with open(full_path, 'w') as file:
                file.write(file_content)
            return jsonify({"status": "File created", "path": path + file_name})
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No file name or content provided"}), 400
    
@app.route('/api/delete_file', methods=['POST'])
def delete_file():
    global settings
    path = request.json.get('path')
    if path:
        if has_write_access(path):
            try:
                full_path = os.path.normpath(os.path.join(settings['path'], path))
                if not _within(full_path):
                    return jsonify({"error": "Unauthorized"}), 401
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return jsonify({"status": "File deleted"})
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            except Exception as e:
                return jsonify({"error": "Internal server error"}), 500
        else:
            log("Unauthorized access attempt in deleting file", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No path provided"}), 400

@app.route('/api/rename_file', methods=['POST'])
def rename_file():
    global settings
    old_name = request.json.get('file_name')
    new_name = request.json.get('new_name')
    path = request.json.get('path')
    if old_name and new_name:
        if path:
            full_path = os.path.normpath(os.path.join(settings['path'], path, old_name))
            new_full_path = os.path.normpath(os.path.join(settings['path'], path, new_name))
            if not _within(full_path) or not _within(new_full_path):
                return jsonify({"error": "Unauthorized"}), 401
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
                return jsonify({"error": "Internal server error"}), 500
        else:
            log("Unauthorized access attempt in reneaming file", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No file name provided"}), 400
    
@app.route('/api/get_file', methods=['GET'])
def get_file():
    global settings
    file = request.args.get('file_path')
    if file:
        if has_access(file):
            try:
                full_path = os.path.normpath(os.path.join(settings['path'], file))
                if not _within(full_path):
                    return jsonify({"error": "Unauthorized"}), 401
                if os.path.exists(full_path):
                    mime_type, _ = mimetypes.guess_type(full_path)
                    if mime_type and (mime_type.startswith('video/') or mime_type.startswith('image/') or mime_type.startswith('audio/')):
                        with open(full_path, 'rb') as f:
                            content = f.read()
                        import base64
                        encoded_content = base64.b64encode(content).decode('utf-8')
                        return jsonify({"status": "File content retrieved", "content": encoded_content, "type": "binary"}), 200
                    else:
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            return jsonify({"status": "File content retrieved", "content": content, "type": "text"}), 200
                        except UnicodeDecodeError:
                            with open(full_path, 'rb') as f:
                                content = f.read()
                            import base64
                            encoded_content = base64.b64encode(content).decode('utf-8')
                            return jsonify({"status": "File content retrieved", "content": encoded_content, "type": "binary"}), 200
                else:
                    return jsonify({"error": "Path does not exist"}), 404
            except Exception as e:
                return jsonify({"error": "Internal server error"}), 500
        else:
            log("Unauthorized access attempt in getting file", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No file path provided"}), 400
    
@app.route('/api/edit_file', methods=['POST'])
def edit_file():
    global settings
    path = request.json.get('path')
    file_content = request.json.get('file_content')
    if not file_content:
        file_content = ""
    if path:
        if has_write_access(path):
            try:
                full_path = os.path.normpath(os.path.join(settings['path'], path))
                if not _within(full_path):
                    return jsonify({"error": "Unauthorized"}), 401
                with open(full_path, 'w') as file:
                    file.write(file_content)
                    file.close()
                return jsonify({"status": "File edited", "path": path})
            except Exception as e:
                return jsonify({"error": "Internal server error"}), 500
        else:
            log("Unauthorized acces attempt", request.remote_addr)
            return jsonify({"error": "Unauthorized"}), 401
    else:
        return jsonify({"error": "No path provided"}), 400
    
@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 125')
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
        return jsonify({"error": "Internal server error"}), 500
    
@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    new_settings = request.json
    if new_settings:
        try:
            with open(settings_file, 'r') as file:
                current_settings = json.load(file)
            
            if 'com_password' in current_settings:
                new_settings['com_password'] = current_settings['com_password']
            
            with open(settings_file, 'w') as file:
                json.dump(new_settings, file)
                file.close
            log("Settings updated", request.remote_addr)
            reload_jsons()
            return jsonify({"status": "Settings updated"}), 200
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No settings provided"}), 400

@app.route('/api/get_version', methods=['GET'])
def get_version():
    global settings
    version = settings['version']
    return jsonify ({"version": version})

@app.route('/update_start_exit_program', methods=['POST'])
def update_exit():
    if os.environ.get('ENABLE_UPDATES','false').lower()!='true':
        return jsonify({"error":"Updates disabled"}), 403
    stop_completely()
    return jsonify({"status": "Update started"}), 200

@app.route('/api/update', methods=['POST'])
def update_server():
    if os.environ.get('ENABLE_UPDATES','false').lower()!='true':
        return jsonify({"error":"Updates disabled"}), 403
    def run_update():
        print_status("Update started", "info")
        os.system(f'python3 "{os.path.join(os.path.dirname(__file__), "update.py")}"')
    t = threading.Thread(target=run_update)
    t.start()
    return jsonify({"status": "Update started"}), 200

@app.route('/api/ftp/create_user', methods=['POST'])
def create_ftp_user():
    global settings
    data = request.json
    username = data.get('username')
    password = data.get('password')
    path = data.get('path')
    permissions = data.get('permissions')
    if username and password and permissions:
        try:
            if path:
                full_path = os.path.normpath(os.path.join(settings['path'], path))
            else:
                full_path = os.path.normpath(settings['path'])
            if not full_path.startswith(settings['path']):
                return jsonify({"error": "Unauthorized"}), 401
            if not os.path.exists(full_path):
                return jsonify({"error": "Path does not exist"}), 404
            authorizer.add_user(username, password, full_path, permissions)
            save_ftp_user_to_db(username, password, full_path, permissions)
            log("FTP user created: " + username, request.remote_addr)
            return jsonify({"status": "FTP user created"}), 200
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No username, password or permissions provided"}), 400
    
@app.route('/api/ftp/delete_user', methods=['POST'])
def delete_ftp_user():
    username = request.json.get('username')
    if username:
        try:
            authorizer.remove_user(username)
            delete_ftp_user_from_db(username)
            log("FTP user deleted:" + username, request.remote_addr)
            return jsonify({"status": "FTP user deleted"}), 200
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500

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
        log("FTP users retrived", request.remote_addr)
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/ftp/edit_user', methods=['POST'])
def edit_ftp_user():
    global settings
    username = request.json.get('username')
    password = request.json.get('password')
    path = request.json.get('path')
    permissions = request.json.get('permissions')
    if username:
        try:
            full_path = os.path.normpath(os.path.join(settings['path'], path)) if path else os.path.normpath(settings['path'])
            if not full_path.startswith(settings['path']):
                return jsonify({"error": "Unauthorized"}), 401
            if path and not os.path.exists(full_path):
                return jsonify({"error": "Path does not exist"}), 404
            if password is None or password == "":
                conn = get_users_db_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT password FROM ftp_users WHERE username = ?', (username,))
                result = cursor.fetchone()
                conn.close()
                password = result[0] if result else None
            authorizer.edit_user(username, password, full_path, permissions)
            save_ftp_user_to_db(username, password, full_path, permissions)
            log("FTP user edited: " + username, request.remote_addr)
            return jsonify({"status": "FTP user edited"}), 200
        except ValueError as ve:
            return jsonify({"error": "Internal server error"}), 404
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
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
        return jsonify({"error": "Internal server error"}), 500
    
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
            return jsonify({"error": "Internal server error"}), 500
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
    paths = data.get('paths', '[""]')
    settings_val = ""
    paths_write = data.get('paths_write', '[""]')
    if username and password and name and role:
        try:
            pwd_to_store = password if not needs_rehash(password) else hash_password(password)
            must_change = 1 if (password == username or password.lower() in ['admin','password','123456'] or len(password) < 8) else 0

            api_key = generate_unique_api_key()
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, password, name, ip, role, ftp_users, paths, settings, API_KEY, paths_write, must_change)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, pwd_to_store, name, ip, role, ftp_user, paths, settings_val, api_key, paths_write, must_change))
            conn.commit()
            conn.close()
            log("User created: " + username, request.remote_addr)
            return jsonify({"status": "User created", "API_KEY": api_key}), 200
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
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
                           SELECT role FROM users WHERE username = ?
                           ''', (username,))
            user_result = cursor.fetchone()
            user_role = user_result[0] if user_result else None
            
            cursor.execute('''
                           DELETE FROM users WHERE username = ?
                           ''', (username,))
            conn.commit()
            conn.close()

            if user_role and user_role != 'admin':
                try:
                    with open(roles_file, 'r') as file:
                        current_roles = json.load(file)

                    modified = False
                    for endpoint in current_roles:
                        if user_role in current_roles[endpoint]:
                            current_roles[endpoint].remove(user_role)
                            modified = True

                    if modified:
                        with open(roles_file, 'w') as file:
                            json.dump(current_roles, file)
                        reload_jsons()
                        log(f"Role '{user_role}' removed from roles file after user deletion", request.remote_addr)
                
                except Exception as role_error:
                    log(f"Error updating roles file after user deletion: {str(role_error)}", request.remote_addr)
            
            log("User deleted: " + username, request.remote_addr)
            return jsonify({"status": "User deleted"}), 200
        except Exception as e:
            return jsonify ({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No username provided"}), 400
    
@app.route('/api/user/edit', methods=['POST'])
def edit_user():
    username = request.json.get('username')
    password = request.json.get('password')
    name = request.json.get('name')
    paths = request.json.get('paths', '[""]')
    paths_write = request.json.get('paths_write', '[""]')
    id = request.json.get('id')
    if username and name and id:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            if password:
                pwd_to_store = password if not needs_rehash(password) else hash_password(password)

                cursor.execute('''
                               UPDATE users
                               SET username = ?, password = ?, name = ?, paths = ?, paths_write = ?
                               WHERE id = ?
                               ''', (username, pwd_to_store, name, paths, paths_write, id))
            else:
                cursor.execute('''
                               UPDATE users
                               SET username = ?, name = ?, paths = ?, paths_write = ?
                               WHERE id = ?
                               ''', (username, name, paths, paths_write, id))
            log("User edited: " + username, request.remote_addr)
            conn.commit()
            conn.close()
            return jsonify({"status": "User edited"}), 200
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No username, name, role or id provided"}), 400

@app.route('/api/user/login', methods=['POST'])
@limiter.limit("1/second", override_defaults=False)
@limiter.limit("5/minute", override_defaults=False)
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if username and password:
        try:
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()
            if user:
                stored = user[2]
                verified = verify_password(stored, password)
                if verified and needs_rehash(stored):
                    new_hash = hash_password(password)
                    conn2 = get_users_db_connection()
                    cur2 = conn2.cursor()
                    cur2.execute('UPDATE users SET password = ? WHERE id = ?', (new_hash, user[0]))
                    conn2.commit()
                    conn2.close()
                if verified:
                    if len(user) > 11 and user[11] == 1:
                        return jsonify({"error": "Password change required"}), 403
                    log("User logged in: " + username, request.remote_addr)
                    payload = {
                        'user_id': user[0],
                        'username': user[1],
                        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
                    }
                    token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
                    return jsonify({"token": token}), 200
            log("Invalid login attempt: " + username, request.remote_addr)
            return jsonify({"error": "Invalid username or password"}), 401
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No username or password provided"}), 400

@app.route('/api/user/get_self', methods=['GET'])
def get_user():
    data = g.result
    if data:
        user = {
            "username": data[1],
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

@app.route('/api/user/change_password', methods=['POST'])
def change_password():
    if not hasattr(g, 'result'):
        return jsonify({"error": "Unauthorized"}), 401
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    if not new_password or not old_password:
        return jsonify({"error": "Missing fields"}), 400
    stored = g.result[2]
    if not verify_password(stored, old_password):
        return jsonify({"error": "Invalid credentials"}), 401
    new_hash = hash_password(new_password)
    conn = get_users_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE users SET password = ?, must_change = 0 WHERE id = ?', (new_hash, g.result[0]))
        conn.commit()
        log("Password changed", request.remote_addr)
        return jsonify({"status": "Password changed"}), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()
    
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
                "id": user[0],
                "username": user[1],
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
        return jsonify({"error": "Internal server error"}), 500

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
            pwd_to_store = password if not needs_rehash(password) else hash_password(password)

            updates.append("password = ?")
            params.append(pwd_to_store)
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
                return jsonify({"error": "Internal server error"}), 500
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
        return jsonify ({"error": "Internal server error"}), 500

@app.route('/api/role/edit', methods=['POST'])
def edit_roles():
    new_roles = request.json
    if new_roles:
        try:
            with open(roles_file, 'w') as file:
                json.dump(new_roles, file)
            log('Roles updated', request.remote_addr)
            reload_jsons()
            return jsonify({"status": "Roles update"}), 200
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    else:
        return jsonify({"error": "No roles provided"}), 400

@app.route('/api/role/self', methods=['GET'])
def get_self_role():
    try:
        if not hasattr(g, 'role'):
            return jsonify({"error": "Unauthorized"}), 401
        result = {}
        for endpoint, allowed_roles in roles.items():
            result[endpoint] = (g.role in allowed_roles)
        return jsonify(result), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/', methods=['GET'])
def root():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), 'index.html')

@app.route('/auth', methods=['GET'])
def auth():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), 'login.html')

@app.route('/preview', methods=['GET'])
def preview():
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), 'preview.html')


@app.route('/web/<path:filename>', methods=['GET'])
def serve_static(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web'), filename)

@app.route('/web/assets/<path:filename>', methods=['GET'])
def serve_assets(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'web', 'assets'), filename, mimetype=mimetypes.guess_type(filename)[0])

@app.route('/api/upload', methods=['POST'])
@limiter.limit("30/minute", override_defaults=False)
def upload_file():
    global settings
    file = request.files.get('file')
    path = request.form.get('path', '')
    if not file:
        return jsonify({"error": "No file provided"}), 400
    if path is None:
        path = ''
    if not has_write_access(path):
        return jsonify({"error": "Unauthorized"}), 401
    filename = secure_filename(file.filename)
    dest_dir = os.path.normpath(os.path.join(settings['path'], path)) if path else os.path.normpath(settings['path'])
    if not _within(dest_dir):
        return jsonify({"error": "Unauthorized"}), 401
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.normpath(os.path.join(dest_dir, filename))
    if not _within(dest_path):
        return jsonify({"error": "Unauthorized"}), 401
    try:
        file.save(dest_path)
        log(f"File uploaded", request.remote_addr)
        return jsonify({"status": "File uploaded"}), 200
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500
    
@app.route('/api/download', methods=['GET'])
@limiter.limit("60/minute", override_defaults=False)
def download_file():
    global settings
    file_path = request.args.get('file_path')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
    if not has_access(file_path):
        return jsonify({"error": "Unauthorized"}), 401
    full_path = os.path.normpath(os.path.join(settings['path'], file_path))
    if not _within(full_path):
        return jsonify({"error": "Unauthorized"}), 401
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
                return jsonify({"error": "Internal server error"}), 500
    
    return jsonify({"error": "File or folder does not exist"}), 404

@app.route('/api/cloud/get', methods=['GET'])
def get_cloud_settings():
    cloud_path = os.path.join(os.path.dirname(__file__), 'settings', 'cloud.json')
    if os.path.exists(cloud_path):
        with open(cloud_path, 'r') as f:
            cloud_settings = json.load(f)
        return jsonify(cloud_settings), 200
    return jsonify({"error": "Cloud settings not found"}), 404

@app.route('/api/cloud/manage', methods=['POST'])
def manage_cloud():
    action = request.json.get('action')
    cloud_path = os.path.join(os.path.dirname(__file__), 'settings', 'cloud.json')
    
    if action == 'enable':
        enabled = request.json.get('enabled', False)
        try:
            if os.path.exists(cloud_path):
                with open(cloud_path, 'r') as f:
                    cloud_settings = json.load(f)
            else:
                cloud_settings = {}
            
            cloud_settings['enabled'] = enabled
            
            with open(cloud_path, 'w') as f:
                json.dump(cloud_settings, f, indent=2)
            
            log(f"Cloud {'enabled' if enabled else 'disabled'}", request.remote_addr)
            return jsonify({"status": f"Cloud {'enabled' if enabled else 'disabled'}"}), 200
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    
    elif action == 'delete_auth':
        try:
            if os.path.exists(cloud_path):
                with open(cloud_path, 'r') as f:
                    cloud_settings = json.load(f)
                
                keys_to_remove = ['user_id', 'auth_token', 'username', 'server_id', 'server_name', 'last_authentication', 'server_registered', 'registration_timestamp']
                for key in keys_to_remove:
                    cloud_settings.pop(key, None)
                
                with open(cloud_path, 'w') as f:
                    json.dump(cloud_settings, f, indent=2)
                
                log("Cloud authentication data deleted", request.remote_addr)
                return jsonify({"status": "Authentication data deleted"}), 200
            else:
                return jsonify({"error": "Cloud settings file not found"}), 404
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    
    elif action == 'signup':
        email = request.json.get('email')
        username = request.json.get('username')
        password = request.json.get('password')
        
        if not email or not username or not password:
            return jsonify({"error": "Email, username and password required"}), 400
        
        try:
            if os.path.exists(cloud_path):
                with open(cloud_path, 'r') as f:
                    cloud_settings = json.load(f)
                auth_token = cloud_settings.get('auth_token', '')
            else:
                return jsonify({"error": "Cloud settings not found"}), 404
            
            if not auth_token:
                return jsonify({"error": "Auth token not found in cloud settings"}), 400
            
            signup_data = {
                'email': email,
                'username': username,
                'password': password,
                'auth_token': auth_token
            }
            
            response = requests.post('https://bridge.bbarni.hackclub.app/signup', json=signup_data, timeout=30)
            
            if response.status_code == 200:
                log(f"Cloud signup successful for {username}", request.remote_addr)
                return jsonify({"status": "Signup successful", "data": response.json()}), 200
            else:
                return jsonify({"error": "Signup failed", "details": response.text}), response.status_code
        except requests.RequestException as e:
            return jsonify({"error": "Network error"}), 500
        except Exception as e:
            return jsonify({"error": "Internal server error"}), 500
    
    else:
        return jsonify({"error": "Invalid action"}), 400

def create_app():
    if settings:
        print_status("Settings loaded successfully.", "success")
        initialize_logs_db()
        initialize_users_db()
        flag_weak_passwords()
        load_ftp_users_from_db()
        try:
            if settings['ftp']:
                start_ftp_server()
        except Exception as e:
            print_status(f"Error starting FTP: {e}", "error")
    else:
        print_status("Failed to load settings.", "error")
    return app

if __name__ == "__main__":
    if settings:
        try:
            app.run(host=settings['host'], port=settings['port'], debug=False)
        except Exception as e:
            print_status(f"Error starting server: {e}", "error")
            log("Server start error: " + str(e), "-")
            exit(1)
    else:
        print_status("Please check the documentation for more.", "info")
        exit(1)