from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

connected_servers = {}
pending_commands = {}

@app.route('/')
def index():
    return f'''
    <h1>Shareify Cloud Bridge</h1>
    <p>Connected Local Servers: {len(connected_servers)}</p>
    <ul>
    {''.join([f"<li>{server_id}: {info['name']} (Connected: {info['connected_at']})</li>" for server_id, info in connected_servers.items()])}
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
    else:
        print(f'Client disconnected: {request.sid}')

@socketio.on('register_server')
def handle_server_registration(data):
    server_id = data.get('server_id', str(uuid.uuid4()))
    server_name = data.get('name', f'Server-{server_id[:8]}')
    
    connected_servers[server_id] = {
        'sid': request.sid,
        'name': server_name,
        'connected_at': datetime.now().isoformat(),
        'last_ping': datetime.now().isoformat()
    }
    
    join_room(f'server_{server_id}')
    
    print(f'Local server registered: {server_id} ({server_name})')
    emit('registration_success', {
        'server_id': server_id,
        'message': 'Successfully registered with cloud bridge'
    })

@socketio.on('ping')
def handle_ping(data):
    server_id = data.get('server_id')
    if server_id in connected_servers:
        connected_servers[server_id]['last_ping'] = datetime.now().isoformat()
        emit('pong', {'timestamp': datetime.now().isoformat()})

@socketio.on('command_response')
def handle_command_response(data):
    command_id = data.get('command_id')
    if command_id in pending_commands:
        pending_commands[command_id]['response'] = data
        pending_commands[command_id]['completed'] = True
        print(f'Command {command_id} completed')

def send_command_to_server(server_id, command, command_id=None):
    if server_id not in connected_servers:
        return {'error': 'Server not connected'}, 404
    
    if not command_id:
        command_id = str(uuid.uuid4())
    
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
        'timestamp': datetime.now().isoformat()
    }, room=f'server_{server_id}')
    
    return {
        'command_id': command_id,
        'message': f'Command sent to {server_id}',
        'status': 'pending'
    }

@socketio.on('message')
def handle_message(data):
    print(f'Received message: {data}')
    emit('message', data, broadcast=True)


if __name__ == '__main__':
    print('Starting Socket.IO server...')
    socketio.run(app, host='0.0.0.0', port=5698, debug=True)
