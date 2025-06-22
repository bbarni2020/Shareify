from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import time
import json
import os
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

connected_servers = {}
pending_commands = {}
authenticated_users = {}
rate_limits = defaultdict(list)
users_db_file = 'users_database.json'
users_db_file_path = os.path.join(os.path.dirname(__file__), users_db_file)

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
        return {'error': 'Rate limit exceeded. Too many requests.'}, 429
    
    user_id = None
    users_db = load_users_database()
    for uid, user_info in users_db.items():
        if user_info.get('auth_token') == auth_token:
            user_id = uid
            break
    
    if not user_id:
        return {'error': 'Invalid auth token'}, 401
    
    user_servers = []
    for server_id, server_info in connected_servers.items():
        if server_info.get('owner_user_id') == user_id:
            user_servers.append({
                'server_id': server_id,
                'name': server_info['name'],
                'connected_at': server_info['connected_at'],
                'last_ping': server_info['last_ping']
            })
    
    return {
        'user_id': user_id,
        'servers': user_servers,
        'total_servers': len(user_servers)
    }

@app.route('/cloud/<auth_token>/command')
def test_command_endpoint(auth_token):
    if not check_rate_limit(auth_token, max_requests=20, window_minutes=1):
        return {'error': 'Rate limit exceeded. Too many requests.'}, 429
    
    if request.method == 'GET' and not request.args.get('command'):
        return render_command_dashboard(auth_token)
    
    command = request.args.get('command')
    server_id = request.args.get('server_id')
    
    if not command:
        return {'error': 'Command parameter required'}, 400
    
    user_id = None
    users_db = load_users_database()
    for uid, user_info in users_db.items():
        if user_info.get('auth_token') == auth_token:
            user_id = uid
            break
    
    if not user_id:
        return {'error': 'Invalid auth token'}, 401
    
    if not server_id:
        user_servers = []
        for sid, server_info in connected_servers.items():
            if server_info.get('owner_user_id') == user_id:
                user_servers.append(sid)
        
        if not user_servers:
            return {'error': 'No servers found for this user'}, 404
        
        server_id = user_servers[0]
    
    if server_id not in connected_servers:
        return {'error': 'Server not connected'}, 404
    
    if connected_servers[server_id].get('owner_user_id') != user_id:
        return {'error': 'Not authorized to control this server'}, 403
    
    result = send_command_to_server(server_id, command)
    return result

def render_command_dashboard(auth_token):
    user_id = None
    username = None
    users_db = load_users_database()
    for uid, user_info in users_db.items():
        if user_info.get('auth_token') == auth_token:
            user_id = uid
            username = user_info.get('username')
            break
    
    if not user_id:
        return '<h1>Invalid Auth Token</h1><p>Please check your authentication token.</p>', 401
    
    user_servers = []
    for server_id, server_info in connected_servers.items():
        if server_info.get('owner_user_id') == user_id:
            user_servers.append({
                'id': server_id,
                'name': server_info['name'],
                'connected_at': server_info['connected_at'],
                'last_ping': server_info['last_ping']
            })
    
    server_options = ''.join([
        f'<option value="{server["id"]}">{server["name"]} ({server["id"][:8]})</option>'
        for server in user_servers
    ])
    
    command_history = []
    for cmd_id, cmd_info in pending_commands.items():
        if any(s['id'] == cmd_info['server_id'] for s in user_servers):
            status = 'completed' if cmd_info['completed'] else 'pending'
            command_history.append({
                'id': cmd_id,
                'command': cmd_info['command'],
                'server_id': cmd_info['server_id'],
                'timestamp': cmd_info['timestamp'],
                'status': status,
                'response': cmd_info.get('response', {}) if cmd_info['completed'] else None
            })
    
    command_history.sort(key=lambda x: x['timestamp'], reverse=True)
    command_history = command_history[:10]
    
    history_html = ''.join([
        f'''
        <div class="command-item">
            <div class="command-header">
                <span class="command-text">{cmd['command']}</span>
                <span class="status status-{cmd['status']}">{cmd['status']}</span>
                <span class="timestamp">{cmd['timestamp']}</span>
            </div>
            <div class="command-details">
                Server: {cmd['server_id'][:8]}... | ID: {cmd['id'][:8]}...
            </div>
            {f'<div class="response"><pre>{json.dumps(cmd["response"], indent=2) if cmd["response"] else "No response"}</pre></div>' if cmd['status'] == 'completed' else ''}
        </div>
        '''
        for cmd in command_history
    ])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shareify Cloud Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f7; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .dashboard {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .panel {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .command-form {{ display: flex; flex-direction: column; gap: 15px; }}
            .form-group {{ display: flex; flex-direction: column; }}
            label {{ font-weight: 600; margin-bottom: 5px; color: #333; }}
            input, select, button {{ padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }}
            button {{ background: #007aff; color: white; border: none; cursor: pointer; font-weight: 600; }}
            button:hover {{ background: #0056cc; }}
            .server-list {{ margin-bottom: 20px; }}
            .server-item {{ background: #f8f9fa; padding: 10px; border-radius: 6px; margin-bottom: 8px; }}
            .command-item {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; }}
            .command-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
            .command-text {{ font-family: monospace; background: #e1e1e1; padding: 4px 8px; border-radius: 4px; }}
            .status {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
            .status-completed {{ background: #d4edda; color: #155724; }}
            .status-pending {{ background: #fff3cd; color: #856404; }}
            .timestamp {{ font-size: 12px; color: #666; }}
            .command-details {{ font-size: 12px; color: #666; }}
            .response {{ margin-top: 10px; }}
            .response pre {{ background: #f1f1f1; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; }}
            .quick-commands {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 15px; }}
            .quick-cmd {{ background: #f0f0f0; border: 1px solid #ddd; padding: 8px 12px; border-radius: 6px; cursor: pointer; text-align: center; font-size: 12px; }}
            .quick-cmd:hover {{ background: #e0e0e0; }}
            @media (max-width: 768px) {{ .dashboard {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Shareify Cloud Dashboard</h1>
                <p>Welcome <strong>{username}</strong> | {len(user_servers)} server(s) connected | Auth: {auth_token[:16]}...</p>
            </div>
            
            <div class="dashboard">
                <div class="panel">
                    <h2>Command Console</h2>
                    <form class="command-form" onsubmit="sendCommand(event)">
                        <div class="form-group">
                            <label for="server_select">Target Server:</label>
                            <select id="server_select" name="server_id" required>
                                <option value="">Auto-select first server</option>
                                {server_options}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="command_input">Command:</label>
                            <input type="text" id="command_input" name="command" placeholder="Enter command (e.g., ls, pwd, echo hello)" required>
                        </div>
                        
                        <button type="submit">Execute Command</button>
                    </form>
                    
                    <div class="quick-commands">
                        <div class="quick-cmd" onclick="setCommand('ls -la')">ls -la</div>
                        <div class="quick-cmd" onclick="setCommand('pwd')">pwd</div>
                        <div class="quick-cmd" onclick="setCommand('whoami')">whoami</div>
                        <div class="quick-cmd" onclick="setCommand('date')">date</div>
                        <div class="quick-cmd" onclick="setCommand('uname -a')">uname -a</div>
                        <div class="quick-cmd" onclick="setCommand('df -h')">df -h</div>
                        <div class="quick-cmd" onclick="setCommand('shareify:status')">shareify:status</div>
                        <div class="quick-cmd" onclick="setCommand('shareify:info')">shareify:info</div>
                    </div>
                    
                    <div class="server-list">
                        <h3>Connected Servers ({len(user_servers)})</h3>
                        {''.join([f'<div class="server-item"><strong>{server["name"]}</strong><br><small>ID: {server["id"]}<br>Connected: {server["connected_at"]}<br>Last ping: {server["last_ping"]}</small></div>' for server in user_servers]) or '<p>No servers connected</p>'}
                    </div>
                </div>
                
                <div class="panel">
                    <h2>Command History</h2>
                    <div id="command-history">
                        {history_html or '<p>No command history yet</p>'}
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function setCommand(cmd) {{
                document.getElementById('command_input').value = cmd;
            }}
            
            async function sendCommand(event) {{
                event.preventDefault();
                const formData = new FormData(event.target);
                const params = new URLSearchParams();
                
                for (let [key, value] of formData.entries()) {{
                    if (value) params.append(key, value);
                }}
                
                try {{
                    const response = await fetch(window.location.pathname + '?' + params.toString());
                    const result = await response.json();
                    
                    if (response.ok) {{
                        alert('Command sent successfully!\\nCommand ID: ' + result.command_id);
                        setTimeout(() => location.reload(), 1000);
                    }} else {{
                        alert('Error: ' + result.error);
                    }}
                }} catch (error) {{
                    alert('Network error: ' + error.message);
                }}
            }}
            
            setInterval(() => {{
                location.reload();
            }}, 30000);
        </script>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print('Starting Socket.IO server...')
    socketio.run(app, host='0.0.0.0', port=5698, debug=True)
