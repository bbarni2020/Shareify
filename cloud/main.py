from flask import Flask, request, jsonify
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
from datetime import datetime, timedelta
from collections import defaultdict
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'
app.config['JWT_EXPIRATION_HOURS'] = 24
socketio = SocketIO(app, cors_allowed_origins="*")

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
    expires_at = datetime.utcnow() + timedelta(hours=app.config['JWT_EXPIRATION_HOURS'])
    payload = {
        'user_id': user_id,
        'jwt_id': jwt_id,
        'exp': expires_at,
        'iat': datetime.utcnow()
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
    <p>Connected Local Servers: {len(connected_servers)}</p>
    <p>Authenticated Users: {len(authenticated_users)}</p>
    <p>Total Registered Users: {len(load_users_database())}</p>
    <ul>
    {''.join([f"<li>{server_id}: {info['name']} (Connected: {info['connected_at']})</li>" for server_id, info in connected_servers.items()])}
    </ul>
    <h3>Authenticated Users:</h3>
    <ul>
    {''.join([f"<li>{user_id}: {info['username']} (Last seen: {info['last_activity']})</li>" for user_id, info in authenticated_users.items()])}
    </ul>
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
        'password': hashlib.sha256(password.encode()).hexdigest(),
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
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        for stored_user_id, user_info in users_db.items():
            if (user_info['username'] == username and 
                user_info['password'] == password_hash):

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
        'last_ping': datetime.now().isoformat()
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

def periodic_jwt_cleanup():
    while True:
        time.sleep(3600)
        cleanup_expired_jwts()

if __name__ == '__main__':
    init_sqlite_db()
    cleanup_expired_jwts()
    print('Starting Socket.IO server...')
    threading.Thread(target=periodic_jwt_cleanup, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5698, debug=True)