import socketio
import subprocess
import json
import time
import threading
import uuid
import os
import sys
import argparse
from pathlib import Path
import requests

DEFAULT_CLOUD_URL = "http://127.0.0.1:5698"
DEFAULT_SERVER_ID = None
DEFAULT_SERVER_NAME = None
DEFAULT_HEARTBEAT_INTERVAL = 30
DEFAULT_COMMAND_TIMEOUT = 30

class ShareifyLocalClient:
    def __init__(self, cloud_url=None, server_id=None, server_name=None):
        self.cloud_url = cloud_url or DEFAULT_CLOUD_URL
        
        self.server_id = self._get_or_create_server_id(server_id)
        self.server_name = server_name or DEFAULT_SERVER_NAME or f"Shareify-{self.server_id[:8]}"
        
        self.sio = socketio.Client()
        self.connected = False
        self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
        self.command_timeout = DEFAULT_COMMAND_TIMEOUT
        
        self.setup_handlers()
        
    def setup_handlers(self):
        @self.sio.event
        def connect():
            print(f"Connected to cloud bridge at {self.cloud_url}")
            self.connected = True

            self.sio.emit('register_server', {
                'server_id': self.server_id,
                'name': self.server_name
            })
            
        @self.sio.event
        def disconnect():
            print("Disconnected from cloud bridge")
            self.connected = False
            
        @self.sio.on('registration_success')
        def on_registration(data):
            print(f"Successfully registered: {data['message']}")
            print(f"Server ID: {data['server_id']}")
            
        @self.sio.on('execute_command')
        def on_execute_command(data):
            command_id = data['command_id']
            command = data['command']
            token = data.get('token', None)
            print(f"Received command {command_id}: {command} (token: {token})")

            requests.get(
                f"http://127.0.0.1:6969/command",
                params={'command': command},
                headers={'X-API-KEY': token}
            )
            
            
        @self.sio.on('pong')
        def on_pong(data):
            print(f"Ping response: {data['timestamp']}")
    
    def _get_or_create_server_id(self, provided_id=None):
        
        if provided_id:
            print(f"Using provided server ID: {provided_id}")
            return provided_id
        
        if DEFAULT_SERVER_ID:
            print(f"Using default server ID: {DEFAULT_SERVER_ID}")
            return DEFAULT_SERVER_ID
        
        new_id = str(uuid.uuid4())
        print(f"Generated new server ID: {new_id}")
        return new_id
    
    def get_server_info(self):
        return {
            'server_id': self.server_id,
            'server_name': self.server_name,
            'cloud_url': self.cloud_url,
            'connected': self.connected,
            'heartbeat_interval': self.heartbeat_interval,
            'command_timeout': self.command_timeout
        }
    
    def execute_command(self, command_id, command):
        try:
            print(f"Executing: {command}")
            
            if command.startswith('shareify:'):
                result = self.handle_shareify_command(command[9:])
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.command_timeout
                )
                
                response_data = {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'returncode': result.returncode
                }
            
            self.sio.emit('command_response', {
                'command_id': command_id,
                'success': True,
                'result': response_data if 'response_data' in locals() else result,
                'timestamp': time.time()
            })
            
        except subprocess.TimeoutExpired:
            self.sio.emit('command_response', {
                'command_id': command_id,
                'success': False,
                'error': 'Command timeout',
                'timestamp': time.time()
            })
            
        except Exception as e:
            self.sio.emit('command_response', {
                'command_id': command_id,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            })
    
    def handle_shareify_command(self, command):
        parts = command.split(' ', 1)
        action = parts[0]
        
        if action == 'status':
            return {
                'server_id': self.server_id,
                'server_name': self.server_name,
                'connected': self.connected,
                'uptime': time.time(),
                'platform': sys.platform,
                'heartbeat_interval': self.heartbeat_interval,
                'command_timeout': self.command_timeout
            }
        
        elif action == 'info':
            return self.get_server_info()
        
        elif action == 'restart_service':
            return {'message': 'Shareify service restart initiated'}
        
        elif action == 'get_logs':
            return {'logs': 'Recent log entries...'}
        
        elif action == 'update':
            return {'message': 'Update process started'}
        
        elif action == 'change_name':
            if len(parts) > 1:
                new_name = parts[1].strip()
                old_name = self.server_name
                self.server_name = new_name
                return {'message': f'Server name changed from "{old_name}" to "{new_name}"'}
            else:
                return {'error': 'New name required. Usage: shareify:change_name <new_name>'}
        
        elif action == 'change_id':
            if len(parts) > 1:
                new_id = parts[1].strip()
                old_id = self.server_id
                self.server_id = new_id
                return {'message': f'Server ID changed from "{old_id}" to "{new_id}"'}
            else:
                return {'error': 'New ID required. Usage: shareify:change_id <new_id>'}
        
        elif action == 'generate_new_id':
            old_id = self.server_id
            self.server_id = str(uuid.uuid4())
            return {'message': f'Server ID changed from "{old_id}" to "{self.server_id}"'}
        
        else:
            return {'error': f'Unknown Shareify command: {action}'}
    
    def generate_new_id(self):
        old_id = self.server_id
        self.server_id = str(uuid.uuid4())
        print(f"Server ID changed from {old_id} to {self.server_id}")
        return self.server_id
    
    def set_server_name(self, new_name):
        old_name = self.server_name
        self.server_name = new_name
        print(f"Server name changed from '{old_name}' to '{new_name}'")
        return self.server_name
    
    def set_server_id(self, new_id):
        old_id = self.server_id
        self.server_id = new_id
        print(f"Server ID changed from '{old_id}' to '{new_id}'")
        return self.server_id
    
    def start_heartbeat(self):
        def heartbeat():
            while self.connected:
                try:
                    self.sio.emit('ping', {'server_id': self.server_id})
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    print(f"Heartbeat error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=heartbeat, daemon=True).start()
    
    def connect(self):
        try:
            print(f"Connecting to cloud bridge at {self.cloud_url}")
            self.sio.connect(self.cloud_url)
            self.start_heartbeat()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        if self.connected:
            self.sio.disconnect()
    
    def wait(self):
        try:
            self.sio.wait()
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Shareify Cloud Bridge Client')
    parser.add_argument('--cloud-url', '-u', 
                       default=os.getenv('SHAREIFY_CLOUD_URL', DEFAULT_CLOUD_URL),
                       help=f'Cloud bridge URL (default: {DEFAULT_CLOUD_URL})')
    parser.add_argument('--server-id', '-i',
                       default=os.getenv('SHAREIFY_SERVER_ID', DEFAULT_SERVER_ID),
                       help='Unique server ID (if not provided, will use default or generate new)')
    parser.add_argument('--server-name', '-n',
                       default=os.getenv('SHAREIFY_SERVER_NAME', DEFAULT_SERVER_NAME),
                       help='Server display name')
    parser.add_argument('--heartbeat-interval',
                       type=int,
                       default=DEFAULT_HEARTBEAT_INTERVAL,
                       help=f'Heartbeat interval in seconds (default: {DEFAULT_HEARTBEAT_INTERVAL})')
    parser.add_argument('--command-timeout',
                       type=int,
                       default=DEFAULT_COMMAND_TIMEOUT,
                       help=f'Command execution timeout in seconds (default: {DEFAULT_COMMAND_TIMEOUT})')
    parser.add_argument('--generate-id', '-g',
                       action='store_true',
                       help='Generate a new server ID and exit')
    parser.add_argument('--show-info', '-s',
                       action='store_true',
                       help='Show current server configuration and exit')
    
    args = parser.parse_args()
    
    if args.generate_id:
        new_id = str(uuid.uuid4())
        print(f"Generated new server ID: {new_id}")
        print(f"Use with: --server-id {new_id}")
        print(f"Or set DEFAULT_SERVER_ID = '{new_id}' in the script")
        return
    
    client = ShareifyLocalClient(
        cloud_url=args.cloud_url,
        server_id=args.server_id,
        server_name=args.server_name
    )
    
    if args.heartbeat_interval != DEFAULT_HEARTBEAT_INTERVAL:
        client.heartbeat_interval = args.heartbeat_interval
    if args.command_timeout != DEFAULT_COMMAND_TIMEOUT:
        client.command_timeout = args.command_timeout
    
    if args.show_info:
        info = client.get_server_info()
        print("\n=== Shareify Client Configuration ===")
        for key, value in info.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        return
    
    print(f"\n=== Shareify Cloud Client Starting ===")
    print(f"Cloud URL: {args.cloud_url}")
    print(f"Server ID: {client.server_id}")
    print(f"Server Name: {client.server_name}")
    print(f"Heartbeat Interval: {client.heartbeat_interval}s")
    print(f"Command Timeout: {client.command_timeout}s")
    print("="*50)
    
    if client.connect():
        print("Client started successfully")
        print("Waiting for commands from cloud...")
        client.wait()
    else:
        print("Failed to start client")
        sys.exit(1)

if __name__ == "__main__":
    main()
