from flask import Flask, request, jsonify
import os
import json
import psutil
import sqlite3
import datetime
import mimetypes

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

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'logs.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def log(action, ip):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (timestamp, action, ip)
        VALUES (?, ?, ?)
    ''', (timestamp, action, ip))
    conn.commit()

app = Flask(__name__)

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


if settings:
    print("Settings loaded successfully.")
    initialize_logs_db()
    app.run(host=settings['host'], port=settings['port'], debug=False)
else:
    print("Failed to load settings. Exiting.")
    exit(1)