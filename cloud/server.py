from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import time
import json
import os
import hashlib
import bcrypt
import jwt
import sqlite3
import requests
import threading
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import threading

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = ''
app.config['JWT_SECRET_KEY'] = ''
app.config['JWT_EXPIRATION_HOURS'] = 24
DASHBOARD_PASSWORD = "pass"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

connected_servers = {}
pending_commands = {}
authenticated_users = {}
rate_limits = defaultdict(list)
users_db_file = 'users_database.json'
users_db_file_path = os.path.join(os.path.dirname(__file__), users_db_file)
user_sqlite_db_path = os.path.join(os.path.dirname(__file__), 'user.db')

def check_rate_limit(identifier, max_requests=10, window_minutes=1):
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)
    
    rate_limits[identifier] = [
        req_time for req_time in rate_limits[identifier] 
        if req_time > window_start
    ]
    
    if len(rate_limits[identifier]) >= max_requests:
        return False
    
    rate_limits[identifier].append(now)
    return True

def cleanup_rate_limits():
    now = datetime.now()
    keys_to_remove = []
    
    for identifier, requests in rate_limits.items():
        rate_limits[identifier] = [
            req_time for req_time in requests 
            if req_time > now - timedelta(hours=1)
        ]
        if not rate_limits[identifier]:
            keys_to_remove.append(identifier)
    
    for key in keys_to_remove:
        del rate_limits[key]

def load_users_database():
    if os.path.exists(users_db_file_path):
        try:
            with open(users_db_file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_users_database(users_data):
    with open(users_db_file_path, 'w') as f:
        json.dump(users_data, f, indent=2)

def generate_auth_token(user_id):
    timestamp = str(int(time.time()))
    raw_token = f"{user_id}:{timestamp}:{app.config['SECRET_KEY']}"
    return hashlib.sha256(raw_token.encode()).hexdigest()

def verify_auth_token(user_id, token):
    users_db = load_users_database()
    if user_id in users_db:
        return users_db[user_id].get('auth_token') == token
    return False

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_jwt_token(user_id):
    jwt_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=app.config['JWT_EXPIRATION_HOURS'])
    payload = {
        'user_id': user_id,
        'jwt_id': jwt_id,
        'exp': expires_at,
        'iat': datetime.now(timezone.utc)
    }
    
    store_jwt_session(jwt_id, user_id, expires_at)
    cleanup_expired_jwts()
    
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_id_from_jwt(jwt_token):
    payload = decode_jwt_token(jwt_token)
    if not payload:
        return None
    
    jwt_id = payload.get('jwt_id')
    user_id = payload.get('user_id')
    
    if not jwt_id or not user_id:
        return None
    
    valid_user_id = is_jwt_valid(jwt_id)
    if valid_user_id != user_id:
        return None
    
    return user_id

def init_sqlite_db():
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            auth_token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_activity TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            settings TEXT DEFAULT '{}'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jwt_sessions (
            jwt_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def get_sqlite_user(user_id=None, email=None):
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    elif email:
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    else:
        conn.close()
        return None
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'password': row[3],
            'auth_token': row[4],
            'created_at': row[5],
            'last_activity': row[6],
            'status': row[7],
            'settings': json.loads(row[8]) if row[8] else {}
        }
    return None

def create_sqlite_user(user_id, username, email, password, auth_token):
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (id, username, email, password, auth_token, created_at, last_activity, status, settings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, username, email, password, auth_token,
            datetime.now().isoformat(), datetime.now().isoformat(),
            'active', '{}'
        ))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def update_sqlite_user(user_id, **kwargs):
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    update_fields = []
    values = []
    
    for key, value in kwargs.items():
        if key == 'settings':
            value = json.dumps(value)
        update_fields.append(f"{key} = ?")
        values.append(value)
    
    values.append(user_id)
    
    cursor.execute(f'''
        UPDATE users SET {', '.join(update_fields)} WHERE id = ?
    ''', values)
    
    conn.commit()
    conn.close()

def get_sqlite_user_by_auth_token(auth_token):
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE auth_token = ?', (auth_token,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'password': row[3],
            'auth_token': row[4],
            'created_at': row[5],
            'last_activity': row[6],
            'status': row[7],
            'settings': json.loads(row[8]) if row[8] else {}
        }
    return None

def store_jwt_session(jwt_id, user_id, expires_at):
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO jwt_sessions (jwt_id, user_id, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    ''', (jwt_id, user_id, expires_at.isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

def cleanup_expired_jwts():
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM jwt_sessions 
        WHERE expires_at < ?
    ''', (datetime.now().isoformat(),))
    
    conn.commit()
    conn.close()

def is_jwt_valid(jwt_id):
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id FROM jwt_sessions 
        WHERE jwt_id = ? AND expires_at > ?
    ''', (jwt_id, datetime.now().isoformat()))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_json_user_id_from_auth_token(auth_token):
    users_db = load_users_database()
    for user_id, user_info in users_db.items():
        if user_info.get('auth_token') == auth_token:
            return user_id
    return None

users_db = load_users_database()

@app.route('/')
def index():
    return f'''
    <h1>Shareify Cloud Bridge</h1>
    '''

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('status', {'msg': 'Connected to cloud bridge'})

@socketio.on('disconnect')
def handle_disconnect():
    server_to_remove = None
    for server_id, info in connected_servers.items():
        if info['sid'] == request.sid:
            server_to_remove = server_id
            break
    
    if server_to_remove:
        del connected_servers[server_to_remove]
        print(f'Local server disconnected: {server_to_remove}')

    user_to_update = None
    for user_id, info in authenticated_users.items():
        if info['sid'] == request.sid:
            user_to_update = user_id
            break
    
    if user_to_update:
        users_db = load_users_database()
        if user_to_update in users_db:
            users_db[user_to_update]['last_activity'] = datetime.now().isoformat()
            users_db[user_to_update]['status'] = 'offline'
            save_users_database(users_db)
        
        del authenticated_users[user_to_update]
        print(f'User disconnected: {user_to_update}')
    else:
        print(f'Client disconnected: {request.sid}')

@socketio.on('register_user')
def handle_user_registration(data):
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    if not check_rate_limit(f"register_{client_ip}", max_requests=5, window_minutes=5):
        emit('registration_failed', {'error': 'Rate limit exceeded. Too many registration attempts.'})
        return
    
    username = data.get('username')
    password = data.get('password')
    user_id = data.get('user_id')
    
    if not username or not password:
        emit('registration_failed', {'error': 'Username and password required'})
        return
    
    users_db = load_users_database()

    for existing_user_id, user_info in users_db.items():
        if user_info['username'] == username and existing_user_id != user_id:
            emit('registration_failed', {'error': 'Username already exists'})
            return

    if not user_id:
        user_id = str(uuid.uuid4())

    auth_token = generate_auth_token(user_id)

    users_db[user_id] = {
        'username': username,
        'password': hash_password(password),
        'auth_token': auth_token,
        'created_at': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat(),
        'status': 'online'
    }
    
    save_users_database(users_db)

    authenticated_users[user_id] = {
        'sid': request.sid,
        'username': username,
        'auth_token': auth_token,
        'connected_at': datetime.now().isoformat(),
        'last_activity': datetime.now().isoformat()
    }
    
    join_room(f'user_{user_id}')
    
    print(f'User registered: {user_id} ({username})')
    emit('registration_success', {
        'user_id': user_id,
        'username': username,
        'auth_token': auth_token,
        'message': 'Successfully registered'
    })

@socketio.on('authenticate_user')
def handle_user_authentication(data):
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    if not check_rate_limit(f"auth_{client_ip}", max_requests=10, window_minutes=5):
        emit('authentication_failed', {'error': 'Rate limit exceeded. Too many authentication attempts.'})
        return
    
    user_id = data.get('user_id')
    auth_token = data.get('auth_token')
    username = data.get('username')
    password = data.get('password')
    
    users_db = load_users_database()

    if user_id and auth_token:
        if verify_auth_token(user_id, auth_token):
            user_info = users_db[user_id]

            authenticated_users[user_id] = {
                'sid': request.sid,
                'username': user_info['username'],
                'auth_token': auth_token,
                'connected_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }

            users_db[user_id]['last_activity'] = datetime.now().isoformat()
            users_db[user_id]['status'] = 'online'
            save_users_database(users_db)
            
            join_room(f'user_{user_id}')
            
            print(f'User authenticated via token: {user_id} ({user_info["username"]})')
            emit('authentication_success', {
                'user_id': user_id,
                'username': user_info['username'],
                'auth_token': auth_token,
                'message': 'Successfully authenticated'
            })
            return
    
    if username and password:
        for stored_user_id, user_info in users_db.items():
            if (user_info['username'] == username and 
                verify_password(password, user_info['password'])):

                new_auth_token = generate_auth_token(stored_user_id)
                users_db[stored_user_id]['auth_token'] = new_auth_token
                users_db[stored_user_id]['last_activity'] = datetime.now().isoformat()
                users_db[stored_user_id]['status'] = 'online'
                save_users_database(users_db)

                authenticated_users[stored_user_id] = {
                    'sid': request.sid,
                    'username': username,
                    'auth_token': new_auth_token,
                    'connected_at': datetime.now().isoformat(),
                    'last_activity': datetime.now().isoformat()
                }
                
                join_room(f'user_{stored_user_id}')
                
                print(f'User authenticated via credentials: {stored_user_id} ({username})')
                emit('authentication_success', {
                    'user_id': stored_user_id,
                    'username': username,
                    'auth_token': new_auth_token,
                    'message': 'Successfully authenticated'
                })
                return
    
    emit('authentication_failed', {'error': 'Invalid credentials'})

@socketio.on('register_server')
def handle_server_registration(data):
    user_id = data.get('user_id')
    if user_id and not check_rate_limit(f"server_reg_{user_id}", max_requests=5, window_minutes=1):
        emit('registration_failed', {'error': 'Rate limit exceeded. Too many server registration attempts.'})
        return
    
    auth_token = data.get('auth_token')
    
    if not user_id or not verify_auth_token(user_id, auth_token):
        emit('registration_failed', {'error': 'Authentication required'})
        return
    
    server_id = data.get('server_id', str(uuid.uuid4()))
    server_name = data.get('name', f'Server-{server_id[:8]}')
    
    connected_servers[server_id] = {
        'sid': request.sid,
        'name': server_name,
        'user_id': user_id,
        'auth_token': auth_token,
        'connected_at': datetime.now().isoformat(),
        'last_ping': datetime.now().isoformat(),
        'last_seen': datetime.now().isoformat(),
        'ip': request.environ.get('REMOTE_ADDR', 'Unknown')
    }
    
    join_room(f'server_{server_id}')
    
    print(f'Local server registered: {server_id} ({server_name}) by user {user_id}')
    emit('registration_success', {
        'server_id': server_id,
        'message': 'Successfully registered with cloud bridge'
    })

@socketio.on('ping')
def handle_ping(data):
    server_id = data.get('server_id')
    user_id = data.get('user_id')

    if server_id and server_id in connected_servers:
        connected_servers[server_id]['last_ping'] = datetime.now().isoformat()
        connected_servers[server_id]['last_seen'] = datetime.now().isoformat()
        emit('pong', {'timestamp': datetime.now().isoformat()})
    
    if user_id and user_id in authenticated_users:
        authenticated_users[user_id]['last_activity'] = datetime.now().isoformat()

        users_db = load_users_database()
        if user_id in users_db:
            users_db[user_id]['last_activity'] = datetime.now().isoformat()
            save_users_database(users_db)
        
        emit('pong', {'timestamp': datetime.now().isoformat()})

@socketio.on('command_response')
def handle_command_response(data):
    command_id = data.get('command_id')
    print(f'Received command_response for command_id: {command_id}')
    if command_id in pending_commands:
        pending_commands[command_id]['response'] = data.get('response')
        pending_commands[command_id]['completed'] = True
        print(f'Updated pending_commands for command_id: {command_id}')

def send_command_to_server(server_id, command, command_id=None, method='GET', body=None, shareify_jwt=None):
    if server_id not in connected_servers:
        return {'error': 'Server not connected'}, 404
    
    if not command_id:
        command_id = str(uuid.uuid4())
    
    if body is None:
        body = {}
    
    pending_commands[command_id] = {
        'server_id': server_id,
        'command': command,
        'method': method,
        'body': body,
        'timestamp': datetime.now().isoformat(),
        'completed': False,
        'response': None
    }

    emit_data = {
        'command_id': command_id,
        'command': command,
        'method': method,
        'body': body,
        'timestamp': datetime.now().isoformat()
    }
    
    if shareify_jwt:
        emit_data['shareify_jwt'] = shareify_jwt

    socketio.emit('execute_command', emit_data, room=f'server_{server_id}')
    
    return {
        'command_id': command_id,
        'message': f'Command sent to {server_id}',
        'status': 'pending'
    }

@socketio.on('message')
def handle_message(data):
    user_id = data.get('user_id')
    auth_token = data.get('auth_token')
    
    if user_id and not check_rate_limit(f"msg_{user_id}", max_requests=50, window_minutes=1):
        emit('error', {'message': 'Rate limit exceeded. Too many messages.'})
        return
    
    if not user_id or not verify_auth_token(user_id, auth_token):
        emit('error', {'message': 'Authentication required for messaging'})
        return
    
    print(f'Received message from {user_id}: {data}')
    emit('message', data, broadcast=True)

@app.route('/cloud/<auth_token>/servers')
def list_user_servers(auth_token):
    if not check_rate_limit(auth_token, max_requests=30, window_minutes=1):
        return jsonify({'error': 'Rate limit exceeded. Too many requests.'}), 429
    
    user_servers = []
    json_user_id = get_json_user_id_from_auth_token(auth_token)
    
    for server_id, server_info in connected_servers.items():
        server_user_id = server_info.get('user_id')
        if (server_info.get('auth_token') == auth_token or 
            server_user_id == json_user_id):
            user_servers.append({
                'server_id': server_id,
                'name': server_info['name'],
                'auth_token': server_info['auth_token'],
                'connected_at': server_info['connected_at'],
                'last_ping': server_info['last_ping']
            })
    
    return jsonify({
        'servers': user_servers,
        'total_servers': len(user_servers)
    })

@app.route('/cloud/command', methods=['GET', 'POST'])
def execute_command_on_all_servers():
    shareify_jwt = request.headers.get('X-Shareify-JWT')
    
    jwt_token = request.headers.get('Authorization')
    if jwt_token and jwt_token.startswith('Bearer '):
        jwt_token = jwt_token[7:]
    
    if not jwt_token:
        jwt_token = request.args.get('jwt_token')
    
    if not jwt_token:
        return jsonify({'error': 'JWT token required'}), 401
    
    user_id = get_user_id_from_jwt(jwt_token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired JWT token'}), 401
    
    user = get_sqlite_user(user_id=user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    auth_token = user['auth_token']
    
    if not check_rate_limit(auth_token, max_requests=20, window_minutes=1):
        return jsonify({'error': 'Rate limit exceeded. Too many requests.'}), 429
    
    if request.method == 'POST' and request.is_json:
        json_data = request.get_json()
        command = json_data.get('command')
        method = json_data.get('method', 'GET')
        body = json_data.get('body', {})
    else:
        command = request.args.get('command')
        method = request.args.get('method', 'GET')
        
        body = {}
        if request.args.get('body'):
            try:
                body = json.loads(request.args.get('body'))
            except (json.JSONDecodeError, TypeError):
                body = {}
    
    if not command:
        return jsonify({'error': 'Command parameter required'}), 400
    
    user_servers = []
    json_user_id = get_json_user_id_from_auth_token(auth_token)
    
    for server_id, server_info in connected_servers.items():
        server_user_id = server_info.get('user_id')
        if (server_info.get('auth_token') == auth_token or 
            server_user_id == user_id or 
            server_user_id == json_user_id):
            user_servers.append(server_id)
    
    if not user_servers:
        return jsonify({'error': 'No servers found for this user'}), 404
    
    results = []
    command_ids = []
    
    for server_id in user_servers:
        result = send_command_to_server(server_id, command, method=method, body=body, shareify_jwt=shareify_jwt)
        
        if isinstance(result, tuple):
            error_dict, status_code = result
            continue
            
        command_ids.append(result['command_id'])
        results.append({
            'server_id': server_id,
            'server_name': connected_servers[server_id]['name'],
            'command_id': result['command_id'],
            'status': result['status']
        })

    if not command_ids:
        return jsonify({'error': 'No connected servers found for this user'}), 404
    
    return jsonify({
        'command_ids': command_ids,
        'results': results,
        'message': 'Commands issued successfully'
    })

@app.route('/cloud/response', methods=['GET'])
def get_command_responses():
    jwt_token = request.headers.get('Authorization')
    if jwt_token and jwt_token.startswith('Bearer '):
        jwt_token = jwt_token[7:]
    
    if not jwt_token:
        jwt_token = request.args.get('jwt_token')
    
    if not jwt_token:
        return jsonify({'error': 'JWT token required'}), 401
    
    user_id = get_user_id_from_jwt(jwt_token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired JWT token'}), 401
    
    user = get_sqlite_user(user_id=user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    auth_token = user['auth_token']
    
    if not check_rate_limit(f"response_{auth_token}", max_requests=100, window_minutes=1):
        return jsonify({'error': 'Rate limit exceeded. Too many requests.'}), 429
    
    command_ids = request.args.getlist('command_id')
    if not command_ids:
        return jsonify({'error': 'At least one command_id parameter required'}), 400
    
    responses = {}
    
    for command_id in command_ids:
        if command_id in pending_commands:
            command_data = pending_commands[command_id]
            server_id = command_data['server_id']
            
            if server_id in connected_servers:
                server_info = connected_servers[server_id]
                json_user_id = get_json_user_id_from_auth_token(auth_token)
                server_user_id = server_info.get('user_id')
                
                if (server_info.get('auth_token') == auth_token or 
                    server_user_id == user_id or 
                    server_user_id == json_user_id):
                    
                    responses[command_id] = {
                        'server_id': server_id,
                        'command': command_data['command'],
                        'method': command_data['method'],
                        'timestamp': command_data['timestamp'],
                        'completed': command_data['completed'],
                        'response': command_data['response'],
                        'status': 'completed' if command_data['completed'] else 'pending'
                    }
                else:
                    responses[command_id] = {
                        'error': 'Unauthorized access to command'
                    }
            else:
                responses[command_id] = {
                    'error': 'Server not found or disconnected'
                }
        else:
            responses[command_id] = {
                'error': 'Command not found'
            }
    
    return jsonify({
        'responses': responses
    })

@app.route('/cloud', methods=['GET', 'POST'])
def cloud():
    return "hello"
    
@app.route('/signup', methods=['POST'])
def signup():
    if not check_rate_limit(request.environ.get('REMOTE_ADDR', 'unknown'), max_requests=5, window_minutes=10):
        return jsonify({'error': 'Rate limit exceeded. Too many signup attempts.'}), 429
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    username = data.get('username', email)
    custom_auth_token = data.get('auth_token')
    
    if not email or not password or not custom_auth_token:
        return jsonify({'error': 'Email, password and Shareify token required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    existing_user = get_sqlite_user(email=email)
    if existing_user:
        return jsonify({'error': 'Email already exists'}), 409
    
    user_id = str(uuid.uuid4())
    auth_token = custom_auth_token
    hashed_password = hash_password(password)
    
    success = create_sqlite_user(user_id, username, email, hashed_password, auth_token)
    if not success:
        return jsonify({'error': 'Failed to create user'}), 500
    
    jwt_token = generate_jwt_token(user_id)
    
    return jsonify({
        'user_id': user_id,
        'username': username,
        'email': email,
        'auth_token': auth_token,
        'jwt_token': jwt_token,
        'message': 'User created successfully'
    }), 201

@app.route('/login', methods=['POST'])
def login():
    if not check_rate_limit(request.environ.get('REMOTE_ADDR', 'unknown'), max_requests=10, window_minutes=5):
        return jsonify({'error': 'Rate limit exceeded. Too many login attempts.'}), 429
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = get_sqlite_user(email=email)
    if not user:
        return jsonify({'error': 'Email not found'}), 404
    
    if verify_password(password, user['password']):
        update_sqlite_user(user['id'], 
                          last_activity=datetime.now().isoformat(),
                          status='active')
        
        jwt_token = generate_jwt_token(user['id'])
        
        return jsonify({
            'user_id': user['id'],
            'username': user['username'],
            'email': email,
            'jwt_token': jwt_token,
            'settings': user.get('settings', {}),
            'message': 'Login successful'
        }), 200
    else:
        return jsonify({'error': 'Invalid password'}), 401

@app.route('/user/settings', methods=['GET', 'PUT'])
def user_settings():
    jwt_token = request.headers.get('Authorization')
    if jwt_token and jwt_token.startswith('Bearer '):
        jwt_token = jwt_token[7:]
    
    if not jwt_token:
        return jsonify({'error': 'JWT token required'}), 401
    
    user_id = get_user_id_from_jwt(jwt_token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired JWT token'}), 401
    
    user = get_sqlite_user(user_id=user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    if request.method == 'GET':
        return jsonify({
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'settings': user.get('settings', {}),
            'created_at': user['created_at'],
            'last_activity': user['last_activity']
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        update_data = {'last_activity': datetime.now().isoformat()}
        
        if 'settings' in data:
            update_data['settings'] = data['settings']
        
        if 'username' in data:
            update_data['username'] = data['username']
        
        update_sqlite_user(user['id'], **update_data)
        
        updated_user = get_sqlite_user(user_id=user['id'])
        
        return jsonify({
            'message': 'Settings updated successfully',
            'user_id': user['id'],
            'settings': updated_user['settings']
        })

@app.route('/user/profile', methods=['GET'])
def get_user_profile():
    jwt_token = request.headers.get('Authorization')
    if jwt_token and jwt_token.startswith('Bearer '):
        jwt_token = jwt_token[7:]
    
    if not jwt_token:
        return jsonify({'error': 'JWT token required'}), 401
    
    user_id = get_user_id_from_jwt(jwt_token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired JWT token'}), 401
    
    user = get_sqlite_user(user_id=user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    return jsonify({
        'username': user['username'],
        'email': user['email'],
        'settings': user.get('settings', {}),
        'created_at': user['created_at'],
        'last_activity': user['last_activity'],
        'status': user['status']
    })

@app.route('/user/change-password', methods=['POST'])
def change_password():
    jwt_token = request.headers.get('Authorization')
    if jwt_token and jwt_token.startswith('Bearer '):
        jwt_token = jwt_token[7:]
    
    if not jwt_token:
        return jsonify({'error': 'JWT token required'}), 401
    
    user_id = get_user_id_from_jwt(jwt_token)
    if not user_id:
        return jsonify({'error': 'Invalid or expired JWT token'}), 401
    
    user = get_sqlite_user(user_id=user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON data required'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password required'}), 400
    
    if not verify_password(current_password, user['password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters'}), 400
    
    hashed_new_password = hash_password(new_password)
    
    update_sqlite_user(user['id'], 
                      password=hashed_new_password,
                      last_activity=datetime.now().isoformat())
    
    return jsonify({
        'message': 'Password changed successfully'
    }), 200

def generate_dashboard_jwt():
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        'dashboard': True,
        'exp': expires_at,
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_dashboard_jwt(token):
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload.get('dashboard', False)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return False

@app.route('/dashboard/login', methods=['GET', 'POST'])
def dashboard_login():
    if request.method == 'POST':
        if request.is_json:
            password = request.json.get('password')
        else:
            password = request.form.get('password')
        
        if password == DASHBOARD_PASSWORD:
            token = generate_dashboard_jwt()
            
            if request.is_json:
                return jsonify({'token': token, 'message': 'Login successful'})
            else:
                response = redirect('/dashboard')
                response.set_cookie('dashboard_token', token, httponly=True, max_age=24*3600)
                return response
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid password'}), 401
            else:
                return render_template('dashboard_login.html', error='Invalid password')
    
    return render_template('dashboard_login.html')

@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('dashboard_token')
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if not token or not verify_dashboard_jwt(token):
        return redirect('/dashboard/login')
    
    return render_template('dashboard.html')

@app.route('/dashboard/api/stats')
def dashboard_api_stats():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Authorization token required'}), 401
    
    token = auth_header[7:]
    if not verify_dashboard_jwt(token):
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    cleanup_rate_limits()
    
    return jsonify({
        'total_servers': len(connected_servers),
        'active_commands': len(pending_commands),
        'total_rate_limits': len(rate_limits),
        'connected_servers': list(connected_servers.keys()),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/dashboard/logout', methods=['POST'])
def dashboard_logout():
    response = redirect('/dashboard/login')
    response.set_cookie('dashboard_token', '', expires=0)
    return response

@app.route('/dashboard/servers')
def get_servers():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        server_details = []
        for server_id, server_info in connected_servers.items():
            server_details.append({
                'id': server_id,
                'name': server_info.get('name', f'Server {server_id[:8]}'),
                'connected_at': server_info.get('connected_at', 'Unknown'),
                'last_seen': server_info.get('last_seen', 'Unknown'),
                'auth_token': server_info.get('auth_token', 'Unknown'),
                'status': 'connected'
            })
        
        return jsonify({'success': True, 'servers': server_details})
    except Exception:
        return jsonify({'error': 'Failed to retrieve server list'}), 500

@app.route('/dashboard/servers/<server_id>/disconnect', methods=['POST'])
def disconnect_server(server_id):
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if server_id in connected_servers:
        server_info = connected_servers[server_id]
        server_sid = server_info.get('sid')
        
        try:
            if server_sid:
                socketio.emit('disconnect_request', {'reason': 'Manual disconnect'}, room=server_sid)
                socketio.server.disconnect(server_sid)
        except Exception as e:
            print(f"Error disconnecting server {server_id}: {e}")
        
        try:
            del connected_servers[server_id]
        except KeyError:
            pass
        
        return jsonify({'success': True, 'message': f'Server {server_id} disconnected'})
    
    return jsonify({'error': 'Server not found or already disconnected'}), 404

@app.route('/dashboard/database/sqlite')
def view_sqlite_database():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return redirect('/dashboard/login')
    
    return render_template('database_sqlite.html')

@app.route('/dashboard/database/json')
def view_json_database():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return redirect('/dashboard/login')
    
    return render_template('database_json.html')

@app.route('/dashboard/database/json/data')
def get_json_database_data():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    users_data = load_users_database()
    return jsonify({'success': True, 'data': users_data})

@app.route('/dashboard/database/sqlite/edit', methods=['POST'])
def edit_sqlite_database():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    try:
        conn = sqlite3.connect(user_sqlite_db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            conn.close()
            return jsonify({'success': True, 'columns': columns, 'rows': rows})
        else:
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Query executed successfully'})
    
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 400

@app.route('/dashboard/database/sqlite/row', methods=['POST', 'PUT', 'DELETE'])
def manage_sqlite_row():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    table = data.get('table')
    
    allowed_tables = {'users', 'jwt_sessions'}
    if not table:
        return jsonify({'error': 'Table name required'}), 400
    
    if table not in allowed_tables:
        return jsonify({'error': 'Table not allowed'}), 400
    
    allowed_columns = {
        'users': {'id', 'username', 'email', 'password', 'auth_token', 'created_at', 'last_activity', 'status', 'settings'},
        'jwt_sessions': {'jwt_id', 'user_id', 'expires_at', 'created_at'}
    }
    
    try:
        conn = sqlite3.connect(user_sqlite_db_path)
        cursor = conn.cursor()
        
        if request.method == 'POST':
            columns = data.get('columns', [])
            values = data.get('values', [])
            
            if not columns or not values:
                return jsonify({'error': 'Columns and values required'}), 400
            
            if not all(col in allowed_columns[table] for col in columns):
                return jsonify({'error': 'Invalid column names'}), 400
            
            placeholders = ','.join(['?' for _ in values])
            column_names = ','.join(columns)
            query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
            cursor.execute(query, values)
            
        elif request.method == 'PUT':
            row_id = data.get('id')
            updates = data.get('updates', {})
            
            if not row_id or not updates:
                return jsonify({'error': 'Row ID and updates required'}), 400
            
            if not all(col in allowed_columns[table] for col in updates.keys()):
                return jsonify({'error': 'Invalid column names'}), 400
            
            set_clauses = []
            values = []
            for column, value in updates.items():
                set_clauses.append(f"{column} = ?")
                values.append(value)
            
            values.append(row_id)
            query = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE id = ?"
            cursor.execute(query, values)
            
        elif request.method == 'DELETE':
            row_id = data.get('id')
            
            if not row_id:
                return jsonify({'error': 'Row ID required'}), 400
            
            query = f"DELETE FROM {table} WHERE id = ?"
            cursor.execute(query, [row_id])
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Operation completed successfully'})
        
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 400

@app.route('/dashboard/database/json/row', methods=['POST', 'PUT', 'DELETE'])
def manage_json_row():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    try:
        users_data = load_users_database()
        
        if request.method == 'POST':
            user_id = data.get('user_id', str(uuid.uuid4()))
            user_data = data.get('user_data', {})
            
            if user_id in users_data:
                return jsonify({'error': 'User ID already exists'}), 400
            
            users_data[user_id] = user_data
            
        elif request.method == 'PUT':
            user_id = data.get('user_id')
            user_data = data.get('user_data', {})
            
            if not user_id or user_id not in users_data:
                return jsonify({'error': 'User ID not found'}), 400
            
            users_data[user_id] = user_data
            
        elif request.method == 'DELETE':
            user_id = data.get('user_id')
            
            if not user_id or user_id not in users_data:
                return jsonify({'error': 'User ID not found'}), 400
            
            del users_data[user_id]
        
        save_users_database(users_data)
        return jsonify({'success': True, 'message': 'Operation completed successfully'})
        
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 400

@app.route('/dashboard/database/json/edit', methods=['POST'])
def edit_json_database():
    token = request.cookies.get('dashboard_token')
    if not token or not verify_dashboard_jwt(token):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    new_data = data.get('data')
    
    if not new_data:
        return jsonify({'error': 'Data required'}), 400
    
    try:
        save_users_database(new_data)
        return jsonify({'success': True, 'message': 'JSON database updated successfully'})
    except Exception:
        return jsonify({'error': 'Failed to update database'}), 400

DATABASE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>SQLite Database - Shareify Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; padding: 20px; max-width: 100vw; overflow-x: hidden; }
        .header { background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; font-size: 14px; margin: 2px; }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn-sm { padding: 4px 8px; font-size: 12px; }
        .table-container { background: white; border-radius: 15px; margin-bottom: 20px; overflow: hidden; max-width: 100%; }
        .table-header { background: #f8f9fa; padding: 15px; border-bottom: 1px solid #e9ecef; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
        .editable-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
        .editable-table th, .editable-table td { padding: 4px 8px; text-align: left; border: 1px solid #e9ecef; font-size: 11px; position: relative; word-wrap: break-word; overflow: hidden; }
        .editable-table th { background: #f8f9fa; font-weight: 600; }
        .editable-table tbody tr:hover { background: #f8f9fa; }
        .editable-cell { border: none; background: transparent; width: 100%; padding: 2px; font-size: 11px; box-sizing: border-box; }
        .editable-cell:focus { background: white; border: 1px solid #667eea; outline: none; }
        .row-actions { display: flex; gap: 4px; flex-wrap: wrap; }
        .query-box { background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
        .query-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; resize: vertical; }
        .result-box { background: white; padding: 20px; border-radius: 15px; margin-top: 20px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .add-row-form { background: #f8f9fa; padding: 15px; border-top: 1px solid #e9ecef; }
        .form-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .form-input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; min-width: 100px; }
        .editing-row { background: #fff3cd !important; }
        .table-wrapper { overflow: auto; max-height: 400px; max-width: 100%; }
        @media (max-width: 768px) {
            .editable-table th, .editable-table td { font-size: 10px; padding: 2px 4px; }
            .form-row { flex-direction: column; align-items: stretch; }
            .form-input { margin-bottom: 5px; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>SQLite Database Management</h1>
        <div>
            <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            <a href="/dashboard/database/json" class="btn btn-primary">View JSON DB</a>
        </div>
    </div>
    
    <div class="query-box">
        <h3>Execute Custom SQL Query</h3>
        <textarea id="sqlQuery" class="query-input" rows="4" placeholder="Enter SQL query...">SELECT * FROM users LIMIT 10;</textarea>
        <br><br>
        <button onclick="executeQuery()" class="btn btn-primary">Execute Query</button>
    </div>
    
    <div id="queryResult" class="result-box" style="display: none;">
        <h3>Query Result</h3>
        <div id="resultContent"></div>
    </div>
    
    <div id="statusMessage" class="status" style="display: none;"></div>
    
    {% for table_name, table_info in tables.items() %}
    <div class="table-container">
        <div class="table-header">
            <span>Table: {{ table_name }} ({{ table_info.rows|length }} rows)</span>
            <button onclick="addNewRow('{{ table_name }}')" class="btn btn-success btn-sm">+ Add Row</button>
        </div>
        <div class="table-wrapper">
            <table class="editable-table" id="table-{{ table_name }}">
                <thead>
                    <tr>
                        {% for column in table_info.columns %}
                        <th style="width: {{ (100 / (table_info.columns|length + 1))|round }}%;">{{ column }}</th>
                        {% endfor %}
                        <th style="width: {{ (100 / (table_info.columns|length + 1))|round }}%;">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in table_info.rows %}
                    <tr data-table="{{ table_name }}" data-original-values="{{ row|tojson|e }}">
                        {% for i, cell in enumerate(row) %}
                        <td>
                            <input type="text" class="editable-cell" 
                                   value="{{ cell if cell is not none else '' }}" 
                                   data-column="{{ table_info.columns[i] }}"
                                   onchange="markRowAsEdited(this)">
                        </td>
                        {% endfor %}
                        <td>
                            <div class="row-actions">
                                <button onclick="saveRow(this)" class="btn btn-success btn-sm" style="display: none;">Save</button>
                                <button onclick="cancelEdit(this)" class="btn btn-secondary btn-sm" style="display: none;">Cancel</button>
                                <button onclick="deleteRow(this, '{{ table_name }}')" class="btn btn-danger btn-sm">Delete</button>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="add-row-form" id="add-form-{{ table_name }}" style="display: none;">
            <h4>Add New Row to {{ table_name }}</h4>
            <div class="form-row">
                {% for column in table_info.columns %}
                <input type="text" class="form-input" placeholder="{{ column }}" data-column="{{ column }}">
                {% endfor %}
                <button onclick="saveNewRow('{{ table_name }}')" class="btn btn-success">Save</button>
                <button onclick="cancelNewRow('{{ table_name }}')" class="btn btn-secondary">Cancel</button>
            </div>
        </div>
    </div>
    {% endfor %}
    
    <script>
        function showStatus(message, type = 'success') {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.className = 'status ' + type;
            statusDiv.textContent = message;
            statusDiv.style.display = 'block';
            setTimeout(() => statusDiv.style.display = 'none', 5000);
        }
        
        function markRowAsEdited(input) {
            const row = input.closest('tr');
            row.classList.add('editing-row');
            const actions = row.querySelector('.row-actions');
            actions.querySelector('.btn-success').style.display = 'inline-block';
            actions.querySelector('.btn-secondary').style.display = 'inline-block';
        }
        
        function saveRow(button) {
            const row = button.closest('tr');
            const tableName = row.dataset.table;
            const originalValues = JSON.parse(row.dataset.originalValues);
            const inputs = row.querySelectorAll('.editable-cell');
            const columns = Array.from(inputs).map(input => input.dataset.column);
            const newValues = Array.from(inputs).map(input => input.value);
            
            const setParts = columns.map((col, i) => `${col} = ?`).join(', ');
            const whereClause = columns.map((col, i) => `${col} = ?`).join(' AND ');
            const query = `UPDATE ${tableName} SET ${setParts} WHERE ${whereClause}`;
            
            fetch('/dashboard/database/sqlite/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: query,
                    values: [...newValues, ...originalValues]
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    row.classList.remove('editing-row');
                    row.dataset.originalValues = JSON.stringify(newValues);
                    const actions = row.querySelector('.row-actions');
                    actions.querySelector('.btn-success').style.display = 'none';
                    actions.querySelector('.btn-secondary').style.display = 'none';
                    showStatus('Row updated successfully');
                } else {
                    showStatus('Error updating row: ' + data.error, 'error');
                }
            });
        }
        
        function cancelEdit(button) {
            const row = button.closest('tr');
            const originalValues = JSON.parse(row.dataset.originalValues);
            const inputs = row.querySelectorAll('.editable-cell');
            
            inputs.forEach((input, i) => {
                input.value = originalValues[i] || '';
            });
            
            row.classList.remove('editing-row');
            const actions = row.querySelector('.row-actions');
            actions.querySelector('.btn-success').style.display = 'none';
            actions.querySelector('.btn-secondary').style.display = 'none';
        }
        
        function deleteRow(button, tableName) {
            if (!confirm('Are you sure you want to delete this row?')) return;
            
            const row = button.closest('tr');
            const originalValues = JSON.parse(row.dataset.originalValues);
            const inputs = row.querySelectorAll('.editable-cell');
            const columns = Array.from(inputs).map(input => input.dataset.column);
            
            const whereClause = columns.map((col, i) => `${col} = ?`).join(' AND ');
            const query = `DELETE FROM ${tableName} WHERE ${whereClause}`;
            
            fetch('/dashboard/database/sqlite/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: query,
                    values: originalValues
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    row.remove();
                    showStatus('Row deleted successfully');
                } else {
                    showStatus('Error deleting row: ' + data.error, 'error');
                }
            });
        }
        
        function addNewRow(tableName) {
            const form = document.getElementById('add-form-' + tableName);
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }
        
        function saveNewRow(tableName) {
            const form = document.getElementById('add-form-' + tableName);
            const inputs = form.querySelectorAll('.form-input');
            const columns = Array.from(inputs).map(input => input.dataset.column);
            const values = Array.from(inputs).map(input => input.value);
            
            const placeholders = values.map(() => '?').join(', ');
            const query = `INSERT INTO ${tableName} (${columns.join(', ')}) VALUES (${placeholders})`;
            
            fetch('/dashboard/database/sqlite/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: query,
                    values: values
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showStatus('Row added successfully');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showStatus('Error adding row: ' + data.error, 'error');
                }
            });
        }
        
        function cancelNewRow(tableName) {
            const form = document.getElementById('add-form-' + tableName);
            form.style.display = 'none';
            form.querySelectorAll('.form-input').forEach(input => input.value = '');
        }
        
        function executeQuery() {
            const query = document.getElementById('sqlQuery').value;
            fetch('/dashboard/database/sqlite/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            })
            .then(response => response.json())
            .then(data => {
                const resultDiv = document.getElementById('queryResult');
                const contentDiv = document.getElementById('resultContent');
                
                if (data.success) {
                    if (data.columns && data.rows) {
                        let html = '<div style="overflow: auto; max-height: 400px;"><table class="editable-table"><thead><tr>';
                        data.columns.forEach(col => html += '<th>' + col + '</th>');
                        html += '</tr></thead><tbody>';
                        data.rows.forEach(row => {
                            html += '<tr>';
                            row.forEach(cell => html += '<td>' + (cell || '') + '</td>');
                            html += '</tr>';
                        });
                        html += '</tbody></table></div>';
                        contentDiv.innerHTML = html;
                    } else {
                        contentDiv.innerHTML = '<p style="color: green;">' + data.message + '</p>';
                    }
                } else {
                    contentDiv.innerHTML = '<p style="color: red;">Error: ' + data.error + '</p>';
                }
                
                resultDiv.style.display = 'block';
            });
        }
    </script>
</body>
</html>
'''

JSON_DATABASE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>JSON Database - Shareify Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; padding: 20px; }
        .header { background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .btn { padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; display: inline-block; }
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-success { background: #28a745; color: white; }
        .editor-container { background: white; padding: 20px; border-radius: 15px; }
        .json-editor { width: 100%; height: 500px; font-family: monospace; padding: 15px; border: 1px solid #ddd; border-radius: 5px; resize: vertical; }
        .status { padding: 10px; border-radius: 5px; margin-top: 10px; display: none; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="header">
        <h1>JSON Database Management (users_database.json)</h1>
        <div>
            <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
            <a href="/dashboard/database/sqlite" class="btn btn-primary">View SQLite DB</a>
        </div>
    </div>
    
    <div class="editor-container">
        <h3>Edit JSON Database</h3>
        <p>Be careful when editing the JSON structure. Invalid JSON will cause errors.</p>
        <br>
        <textarea id="jsonEditor" class="json-editor">{{ users_data | tojson(indent=2) }}</textarea>
        <br>
        <button onclick="saveJson()" class="btn btn-success">Save Changes</button>
        <button onclick="location.reload()" class="btn btn-secondary">Reset</button>
        
        <div id="status" class="status"></div>
    </div>
    
    <script>
        function saveJson() {
            const jsonData = document.getElementById('jsonEditor').value;
            const statusDiv = document.getElementById('status');
            
            try {
                const parsed = JSON.parse(jsonData);
                
                fetch('/dashboard/database/json/edit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ data: parsed })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        statusDiv.className = 'status success';
                        statusDiv.textContent = 'Database updated successfully!';
                    } else {
                        statusDiv.className = 'status error';
                        statusDiv.textContent = 'Error: ' + data.error;
                    }
                    statusDiv.style.display = 'block';
                    setTimeout(() => statusDiv.style.display = 'none', 5000);
                });
            } catch (e) {
                statusDiv.className = 'status error';
                statusDiv.textContent = 'Invalid JSON: ' + e.message;
                statusDiv.style.display = 'block';
                setTimeout(() => statusDiv.style.display = 'none', 5000);
            }
        }
    </script>
</body>
</html>
'''

DASHBOARD_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Shareify Dashboard - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        
        .logo {
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        input[type="password"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
            background: white;
        }
        
        input[type="password"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .login-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease;
        }
        
        .login-btn:hover {
            transform: translateY(-2px);
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #c62828;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🔒 Shareify Dashboard</div>
        <div class="subtitle">Admin Access Required</div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required autofocus>
            </div>
            <button type="submit" class="login-btn">Access Dashboard</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Shareify Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
            padding: 20px;
        }
        
        .header {
            background: white;
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .timestamp {
            color: #666;
            font-size: 14px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
            display: inline-block;
        }
        
        .btn-primary { background: #667eea; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            text-align: center;
        }
        
        .stat-number {
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .servers { color: #4CAF50; }
        .commands { color: #FF9800; }
        .limits { color: #F44336; }
        
        .section {
            background: white;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 30px;
            overflow: hidden;
        }
        
        .section-header {
            background: #f8f9fa;
            padding: 20px 30px;
            border-bottom: 1px solid #e9ecef;
            font-weight: 600;
            color: #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .section-content {
            padding: 30px;
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table th,
        .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }
        
        .table tr:hover {
            background: #f8f9fa;
        }
        
        .status-online {
            color: #4CAF50;
            font-weight: 600;
        }
        
        .empty-state {
            text-align: center;
            color: #666;
            padding: 40px;
        }
        
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s ease;
        }
        
        .refresh-btn:hover {
            background: #5a6fd8;
        }
        
        .action-buttons {
            display: flex;
            gap: 8px;
        }
        
        .server-id {
            font-family: monospace;
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 10px;
                text-align: center;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .table {
                font-size: 14px;
            }
            
            .section-content {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">📊 Shareify Dashboard</div>
        <div class="header-right">
            <div class="timestamp">Last updated: {{ current_time }}</div>
            <a href="/dashboard/database/sqlite" class="btn btn-primary">Manage SQLite DB</a>
            <a href="/dashboard/database/json" class="btn btn-secondary">Manage JSON DB</a>
            <form method="POST" action="/dashboard/logout" style="display: inline;">
                <button type="submit" class="btn btn-danger">Logout</button>
            </form>
        </div>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number servers">{{ total_servers }}</div>
            <div class="stat-label">Connected Servers</div>
        </div>
        <div class="stat-card">
            <div class="stat-number commands">{{ active_commands }}</div>
            <div class="stat-label">Active Commands</div>
        </div>
        <div class="stat-card">
            <div class="stat-number limits">{{ total_rate_limits }}</div>
            <div class="stat-label">Rate Limit Entries</div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-header">
            Connected Servers
            <div>
                <button class="refresh-btn" onclick="location.reload()">Refresh</button>
            </div>
        </div>
        <div class="section-content">
            {% if server_details %}
            <table class="table">
                <thead>
                    <tr>
                        <th>Server ID</th>
                        <th>Name</th>
                        <th>Auth Token</th>
                        <th>Connected At</th>
                        <th>Last Seen</th>
                        <th>Pending Commands</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for server in server_details %}
                    <tr>
                        <td><span class="server-id">{{ server.id[:12] }}...</span></td>
                        <td>{{ server.name }}</td>
                        <td><span class="server-id">{{ server.auth_token[:8] }}...</span></td>
                        <td>{{ server.connected_at }}</td>
                        <td class="status-online">{{ server.last_seen }}</td>
                        <td>{{ server.pending_commands }}</td>
                        <td>
                            <div class="action-buttons">
                                <button class="btn btn-warning" onclick="disconnectServer('{{ server.id }}')">Disconnect</button>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">No servers currently connected</div>
            {% endif %}
        </div>
    </div>
    
    <div class="section">
        <div class="section-header">Rate Limit Status</div>
        <div class="section-content">
            {% if rate_limit_details %}
            <table class="table">
                <thead>
                    <tr>
                        <th>Identifier</th>
                        <th>Request Count</th>
                        <th>Last Request</th>
                    </tr>
                </thead>
                <tbody>
                    {% for limit in rate_limit_details %}
                    <tr>
                        <td><code>{{ limit.identifier }}</code></td>
                        <td>{{ limit.request_count }}</td>
                        <td>{{ limit.last_request }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">No active rate limits</div>
            {% endif %}
        </div>
    </div>
    
    <script>
        function disconnectServer(serverId) {
            if (confirm('Are you sure you want to disconnect this server?')) {
                fetch('/dashboard/servers/' + serverId + '/disconnect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Server disconnected successfully');
                        location.reload();
                    } else {
                        alert('Error: ' + data.error);
                    }
                });
            }
        }
        
        setTimeout(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
'''

def periodic_cleanup():
    """Periodic cleanup function that runs JWT and rate limit cleanup"""
    while True:
        time.sleep(3600)
        cleanup_expired_jwts()
        cleanup_rate_limits()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Periodic cleanup completed")

def create_app():
    init_sqlite_db()
    cleanup_expired_jwts()
    cleanup_rate_limits()
    threading.Thread(target=periodic_cleanup, daemon=True).start()
    return app

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5698
    
    application = create_app()
    print(f'Starting Shareify bridge server on: port {port} (http://{host}:{port})')
    socketio.run(application, host=host, port=port, debug=False)