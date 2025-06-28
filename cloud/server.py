from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import time
import json
import os
import hashlib
import bcrypt
import jwt
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
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
        'owner_user_id': user_id,
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
    if command_id in pending_commands:
        pending_commands[command_id]['response'] = data
        pending_commands[command_id]['completed'] = True
        print(f'Command {command_id} completed')

def send_command_to_server(server_id, command, command_id=None, method='GET', body=None):
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

    socketio.emit('execute_command', {
        'command_id': command_id,
        'command': command,
        'method': method,
        'body': body,
        'timestamp': datetime.now().isoformat()
    }, room=f'server_{server_id}')
    
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
    
    user_ids = []

    users_db = load_users_database()
    for uid, user_info in users_db.items():
        if user_info.get('auth_token') == auth_token:
            user_ids.append(uid)

    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE auth_token = ?', (auth_token,))
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        user_ids.append(row[0])
    
    if not user_ids:
        return jsonify({'error': 'Invalid auth token'}), 401
    
    user_servers = []
    for server_id, server_info in connected_servers.items():
        if server_info.get('owner_user_id') in user_ids:
            user_servers.append({
                'server_id': server_id,
                'name': server_info['name'],
                'owner_user_id': server_info['owner_user_id'],
                'connected_at': server_info['connected_at'],
                'last_ping': server_info['last_ping']
            })
    
    return jsonify({
        'user_ids': user_ids,
        'servers': user_servers,
        'total_servers': len(user_servers)
    })

@app.route('/cloud', methods=['GET', 'POST'])
def execute_command_on_all_servers():
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
    
    user_ids = []
    
    users_db = load_users_database()
    for uid, user_info in users_db.items():
        if user_info.get('auth_token') == auth_token:
            user_ids.append(uid)
    
    conn = sqlite3.connect(user_sqlite_db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE auth_token = ?', (auth_token,))
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        user_ids.append(row[0])
    
    if not user_ids:
        return jsonify({'error': 'No servers found for this auth token'}), 404
    
    auth_token_servers = []
    for server_id, server_info in connected_servers.items():
        if server_info.get('owner_user_id') in user_ids:
            auth_token_servers.append(server_id)
    
    if not auth_token_servers:
        return jsonify({'error': 'No servers found for this auth token'}), 404
    
    results = []
    for server_id in auth_token_servers:
        result = send_command_to_server(server_id, command, method=method, body=body)
        results.append({
            'server_id': server_id,
            'server_name': connected_servers[server_id]['name'],
            'result': result
        })
    
    return jsonify({
        'auth_token': auth_token,
        'user_ids': user_ids,
        'command': command,
        'method': method,
        'body': body,
        'servers_targeted': len(auth_token_servers),
        'results': results
    })

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
            'auth_token': user['auth_token'],
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
                return render_template_string(DASHBOARD_LOGIN_TEMPLATE, error="Invalid password")
    
    return render_template_string(DASHBOARD_LOGIN_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('dashboard_token')
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
    
    if not token or not verify_dashboard_jwt(token):
        return redirect('/dashboard/login')
    
    cleanup_rate_limits()
    
    total_servers = len(connected_servers)
    active_commands = len(pending_commands)
    total_rate_limits = len(rate_limits)
    
    server_details = []
    for server_id, server_info in connected_servers.items():
        server_details.append({
            'id': server_id,
            'name': server_info.get('name', 'Unknown'),
            'ip': server_info.get('ip', 'Unknown'),
            'connected_at': server_info.get('connected_at', 'Unknown'),
            'last_seen': server_info.get('last_seen', 'Unknown'),
            'pending_commands': len([cmd for cmd in pending_commands.values() if cmd.get('server_id') == server_id])
        })
    
    rate_limit_details = []
    for identifier, requests in rate_limits.items():
        rate_limit_details.append({
            'identifier': identifier,
            'request_count': len(requests),
            'last_request': max(requests).strftime('%Y-%m-%d %H:%M:%S') if requests else 'None'
        })
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                  total_servers=total_servers,
                                  active_commands=active_commands,
                                  total_rate_limits=total_rate_limits,
                                  server_details=server_details,
                                  rate_limit_details=rate_limit_details,
                                  current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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
        
        .timestamp {
            color: #666;
            font-size: 14px;
        }
        
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
        <div class="timestamp">Last updated: {{ current_time }}</div>
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
            <button class="refresh-btn" onclick="location.reload()">Refresh</button>
        </div>
        <div class="section-content">
            {% if server_details %}
            <table class="table">
                <thead>
                    <tr>
                        <th>Server ID</th>
                        <th>Name</th>
                        <th>IP Address</th>
                        <th>Connected At</th>
                        <th>Last Seen</th>
                        <th>Pending Commands</th>
                    </tr>
                </thead>
                <tbody>
                    {% for server in server_details %}
                    <tr>
                        <td><code>{{ server.id[:8] }}...</code></td>
                        <td>{{ server.name }}</td>
                        <td>{{ server.ip }}</td>
                        <td>{{ server.connected_at }}</td>
                        <td class="status-online">{{ server.last_seen }}</td>
                        <td>{{ server.pending_commands }}</td>
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
        // Auto-refresh every 30 seconds
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