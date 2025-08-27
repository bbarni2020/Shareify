import socketio
import subprocess
import json
import time
import threading
import uuid
import os
import sys
from pathlib import Path
import requests
from colorama import init, Fore, Back, Style


def print_status(message, status_type="info"):
    if status_type == "success":
        print(Fore.GREEN + message)
    elif status_type == "error":
        print(Fore.RED + message)
    elif status_type == "warning":
        print(Fore.YELLOW + message)
    else:
        print(Fore.BLUE + message)

def load_cloud_config():
    settings_dir = Path(__file__).parent / "settings"
    cloud_config_path = settings_dir / "cloud.json"
    
    if cloud_config_path.exists():
        try:
            with open(cloud_config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_cloud_config(config_data):
    settings_dir = Path(__file__).parent / "settings"
    settings_dir.mkdir(exist_ok=True)
    cloud_config_path = settings_dir / "cloud.json"
    
    with open(cloud_config_path, 'w') as f:
        json.dump(config_data, f, indent=2)

DEFAULT_CLOUD_URL = "https://bridge.bbarni.hackclub.app"
DEFAULT_SERVER_ID = None
DEFAULT_SERVER_NAME = None
DEFAULT_HEARTBEAT_INTERVAL = 30
DEFAULT_COMMAND_TIMEOUT = 30

class ShareifyLocalClient:
    def __init__(self, cloud_url="https://bridge.bbarni.hackclub.app", server_id=None, server_name=None, user_id=None, auth_token=None, username=None, password=None):
        self.cloud_url = DEFAULT_CLOUD_URL
        
        self.cloud_config = load_cloud_config()
        
        self.server_id = self._get_or_create_server_id(server_id)
        self.server_name = server_name or DEFAULT_SERVER_NAME or f"Shareify-{self.server_id[:8]}"
        
        self.user_id = user_id or self.cloud_config.get('user_id')
        self.auth_token = auth_token or self.cloud_config.get('auth_token')
        self.username = username or self.cloud_config.get('username')
        self.password = password or self.cloud_config.get('password')
        self.enabled = self.cloud_config.get('enabled', True)
        self.authenticated = False
        
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1,
            reconnection_delay_max=5,
            logger=False,
            engineio_logger=False
        )
        self.connected = False
        self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
        self.command_timeout = DEFAULT_COMMAND_TIMEOUT
        self.last_successful_ping = time.time()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
        self.setup_handlers()
        
    def setup_handlers(self):
        @self.sio.event
        def connect():
            print(f"Connected to cloud bridge at {self.cloud_url}")
            self.connected = True
            self.authenticate_user()
            
        @self.sio.event
        def disconnect():
            print("Disconnected from cloud bridge")
            self.connected = False
            self.authenticated = False
            
        @self.sio.on('authentication_success')
        def on_auth_success(data):
            print(f"Authentication successful: {data['username']}")
            self.user_id = data['user_id']
            self.auth_token = data.get('auth_token')
            self.authenticated = True
            
            config_data = {
                'user_id': self.user_id,
                'auth_token': self.auth_token,
                'username': data['username'],
                'server_id': self.server_id,
                'server_name': self.server_name,
                'cloud_url': self.cloud_url,
                'enabled': self.enabled,
                'last_authentication': time.time()
            }
            save_cloud_config(config_data)
            print(f"Authentication data saved to cloud.json")
            
            self.register_server()
            
        @self.sio.on('authentication_failed')
        def on_auth_failed(data):
            print_status(f"Authentication failed: {data['error']}", "error")
            self.authenticated = False
            
            if self.auth_token and self.username and self.password:
                print_status("Auth token failed, trying username/password fallback...", "warning")
                self.sio.emit('authenticate_user', {
                    'username': self.username,
                    'password': self.password
                })
            else:
                print_status("No fallback credentials available", "error")
            
        @self.sio.on('registration_success')
        def on_registration_success(data):
            if 'server_id' in data:
                print(f"Server registration successful: {data['message']}")
                print(f"Server ID: {data['server_id']}")
                
                config_data = load_cloud_config()
                config_data.update({
                    'server_registered': True,
                    'registration_timestamp': time.time(),
                    'server_id': self.server_id,
                    'server_name': self.server_name,
                    'user_id': self.user_id,
                    'auth_token': self.auth_token,
                    'username': self.username,
                    'cloud_url': self.cloud_url,
                    'enabled': self.enabled
                })
                save_cloud_config(config_data)
                print(f"Server registration data saved to cloud.json")
            else:
                print(f"User registration successful: {data['username']}")
                self.user_id = data['user_id']
                self.auth_token = data.get('auth_token')
                self.authenticated = True
                
                config_data = {
                    'user_id': self.user_id,
                    'auth_token': self.auth_token,
                    'username': data['username'],
                    'password': self.password,
                    'server_id': self.server_id,
                    'server_name': self.server_name,
                    'cloud_url': self.cloud_url,
                    'enabled': self.enabled,
                    'user_registered': True,
                    'user_registration_timestamp': time.time()
                }
                save_cloud_config(config_data)
                print(f"User registration data saved to cloud.json")
                
                self.register_server()
            
        @self.sio.on('registration_failed')
        def on_registration_failed(data):
            if 'server_id' in str(data):
                print(f"Server registration failed: {data['error']}")
            else:
                print(f"User registration failed: {data['error']}")
                self.authenticated = False
            
        @self.sio.on('execute_command')
        def on_execute_command(data):
            command_id = data['command_id']
            command = data['command']
            method = data.get('method', 'GET')
            body = data.get('body', {})
            timestamp = data.get('timestamp')
            shareify_jwt = data.get('shareify_jwt')
            print(f"Received command {command_id}: {command} (method: {method})")

            try:
                self.execute_api_request(command_id, command, method, body, shareify_jwt)
            except Exception as e:
                print(f"Failed to handle command: {e}")
                if self.sio.connected:
                    try:
                        self.sio.emit('command_response', {
                            'command_id': command_id,
                            'response': {'error': str(e)}
                        })
                    except Exception as emit_error:
                        print(f"Failed to emit command error: {emit_error}")
            
            
        @self.sio.on('pong')
        def on_pong(data):
            self.last_successful_ping = time.time()
            self.reconnect_attempts = 0
            print(f"Ping response: {data.get('timestamp', 'no timestamp')}")
    
    def authenticate_user(self):
        if self.user_id and self.auth_token:
            print_status(f"Authenticating with saved token for user: {self.user_id}", "info")
            self.sio.emit('authenticate_user', {
                'user_id': self.user_id,
                'auth_token': self.auth_token
            })
        elif self.username and self.password:
            print_status(f"Authenticating with username/password for user: {self.username}", "info")
            self.sio.emit('authenticate_user', {
                'username': self.username,
                'password': self.password
            })
        else:
            print_status("No authentication credentials found, registering new user", "warning")
            new_username = f"shareify_user_{str(uuid.uuid4())[:8]}"
            new_password = str(uuid.uuid4())
            self.sio.emit('register_user', {
                'username': new_username,
                'password': new_password
            })
            self.username = new_username
            self.password = new_password
    
    def register_server(self):
        if not self.authenticated:
            print("Cannot register server: not authenticated")
            return
            
        self.sio.emit('register_server', {
            'server_id': self.server_id,
            'name': self.server_name,
            'user_id': self.user_id,
            'auth_token': self.auth_token
        })
    
    def _get_or_create_server_id(self, provided_id=None):
        if provided_id:
            print_status(f"Using provided server ID: {provided_id}", "info")
            return provided_id
        
        saved_server_id = self.cloud_config.get('server_id')
        if saved_server_id:
            print_status(f"Using saved server ID from cloud.json: {saved_server_id}", "success")
            return saved_server_id
        
        if DEFAULT_SERVER_ID:
            print_status(f"Using default server ID: {DEFAULT_SERVER_ID}", "info")
            return DEFAULT_SERVER_ID
        
        new_id = str(uuid.uuid4())
        print_status(f"Generated new server ID: {new_id}", "warning")
        return new_id
    
    def get_server_info(self):
        return {
            'server_id': self.server_id,
            'server_name': self.server_name,
            'cloud_url': self.cloud_url,
            'connected': self.connected,
            'enabled': self.enabled,
            'heartbeat_interval': self.heartbeat_interval,
            'command_timeout': self.command_timeout
        }
    
    def handle_shareify_command(self, command):
        parts = command.split(' ', 1)
        action = parts[0]
        
        if action == 'status':
            return {
                'server_id': self.server_id,
                'server_name': self.server_name,
                'connected': self.connected,
                'enabled': self.enabled,
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
                self.set_server_name(new_name)
                return {'message': f'Server name changed from "{old_name}" to "{new_name}" and saved'}
            else:
                return {'error': 'New name required. Usage: shareify:change_name <new_name>'}
        
        elif action == 'change_id':
            if len(parts) > 1:
                new_id = parts[1].strip()
                old_id = self.server_id
                self.set_server_id(new_id)
                return {'message': f'Server ID changed from "{old_id}" to "{new_id}" and saved'}
            else:
                return {'error': 'New ID required. Usage: shareify:change_id <new_id>'}
        
        elif action == 'generate_new_id':
            old_id = self.server_id
            new_id = self.generate_new_id()
            return {'message': f'Server ID changed from "{old_id}" to "{new_id}" and saved'}
        
        elif action == 'enable':
            self.set_enabled(True)
            return {'message': 'Cloud connection enabled'}
        
        elif action == 'disable':
            self.set_enabled(False)
            return {'message': 'Cloud connection disabled'}
        
        elif action == 'toggle':
            new_state = not self.enabled
            self.set_enabled(new_state)
            return {'message': f'Cloud connection {"enabled" if new_state else "disabled"}'}
        
        else:
            return {'error': f'Unknown Shareify command: {action}'}
    
    def generate_new_id(self):
        old_id = self.server_id
        self.server_id = str(uuid.uuid4())
        
        config_data = load_cloud_config()
        config_data['server_id'] = self.server_id
        save_cloud_config(config_data)
        
        print_status(f"Server ID changed from {old_id} to {self.server_id} and saved to cloud.json", "success")
        return self.server_id
    
    def set_server_name(self, new_name):
        old_name = self.server_name
        self.server_name = new_name

        config_data = load_cloud_config()
        config_data['server_name'] = new_name
        save_cloud_config(config_data)
        
        print_status(f"Server name changed from '{old_name}' to '{new_name}' and saved to cloud.json", "success")
        return self.server_name
    
    def set_server_id(self, new_id):
        old_id = self.server_id
        self.server_id = new_id

        config_data = load_cloud_config()
        config_data['server_id'] = new_id
        save_cloud_config(config_data)
        
        print_status(f"Server ID changed from '{old_id}' to '{new_id}' and saved to cloud.json", "success")
        return self.server_id
    
    def set_enabled(self, enabled):
        self.enabled = enabled
        config_data = load_cloud_config()
        config_data['enabled'] = enabled
        save_cloud_config(config_data)
        print(f"Cloud connection {'enabled' if enabled else 'disabled'}")
        return self.enabled
    
    def is_enabled(self):
        return self.enabled
    
    def start_heartbeat(self):
        def heartbeat():
            while self.connected and self.enabled:
                try:
                    if self.authenticated:
                        self.sio.emit('ping', {
                            'server_id': self.server_id,
                            'user_id': self.user_id,
                            'timestamp': time.time()
                        })

                        if time.time() - self.last_successful_ping > (self.heartbeat_interval * 6):
                            print_status("No pong received for extended period, connection might be dead", "warning")
                            if self.reconnect_attempts < self.max_reconnect_attempts:
                                self.reconnect_attempts += 1
                                print_status(f"Attempting reconnection ({self.reconnect_attempts}/{self.max_reconnect_attempts})", "info")
                                self.disconnect()
                                time.sleep(5)
                                if self.connect():
                                    print_status("Reconnection successful", "success")
                                    continue
                            else:
                                print_status("Max reconnection attempts reached", "error")
                                break
                    
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    print_status(f"Heartbeat error: {e}", "error")
                    time.sleep(self.heartbeat_interval)
                    if not self.connected:
                        break
        
        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()
    
    def connect(self):
        if not self.enabled:
            print("Cloud connection is disabled. Use 'shareify:enable' to enable it.")
            return False

        try:
            if self.connected:
                self.sio.disconnect()
                time.sleep(2)
        except:
            pass
            
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                print_status(f"Connecting to cloud bridge at {self.cloud_url} (attempt {attempt + 1}/{max_retries})")

                self.sio.connect(
                    self.cloud_url, 
                    wait_timeout=15,
                    socketio_path='/socket.io/',
                    headers={'User-Agent': f'Shareify-Client/{self.server_id}'}
                )
                self.start_heartbeat()
                return True
            except Exception as e:
                print_status(f"Connection attempt {attempt + 1} failed: {e}", "error")
                if attempt < max_retries - 1:
                    print_status(f"Retrying in {retry_delay} seconds...", "warning")
                    time.sleep(retry_delay)
                    retry_delay += 2
                else:
                    print_status(f"All connection attempts failed", "error")
                    return False
    
    def disconnect(self):
        print_status("Disconnecting from cloud bridge...", "info")
        self.connected = False
        self.authenticated = False
        if self.sio.connected:
            try:
                self.sio.disconnect()
                time.sleep(1)
            except Exception as e:
                print_status(f"Error during disconnect: {e}", "warning")
    
    def wait(self):
        try:
            while self.connected and self.enabled:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.disconnect()

    def execute_api_request(self, command_id, url, method='GET', body=None, shareify_jwt=None):
        try:
            base_url = "http://127.0.0.1:6969/api"
            
            if url.startswith('/'):
                full_url = base_url + url
            else:
                full_url = base_url + '/' + url
            
            print(f"Making {method} request to: {full_url}")
            
            allowed_endpoints = [
                '/resources', 'resources',
                '/is_up', 'is_up',
                '/user/get_self', 'user/get_self',
                '/user/login', 'user/login',
                '/get_logs', '/finder', '/get_file'
            ]
            if not any(url == ep or url.startswith(ep) for ep in allowed_endpoints):
                if self.sio.connected:
                    try:
                        self.sio.emit('command_response', {
                            'command_id': command_id,
                            'response': {'error': 'Not allowed (security reasons) to access this endpoint.'}
                        })
                    except Exception as emit_error:
                        print(f"Failed to emit security error: {emit_error}")
                return

            headers = {'Content-Type': 'application/json'}
            
            if shareify_jwt:
                headers['Authorization'] = f'Bearer {shareify_jwt}'
            
            if method.upper() == 'GET':
                if isinstance(body, dict) and body:
                    import urllib.parse
                    query_string = urllib.parse.urlencode(body)
                    if '?' in full_url:
                        full_url = f"{full_url}&{query_string}"
                    else:
                        full_url = f"{full_url}?{query_string}"
                response = requests.get(full_url, headers=headers, timeout=self.command_timeout)
            elif method.upper() == 'POST':
                response = requests.post(full_url, json=body, headers=headers, timeout=self.command_timeout)
            elif method.upper() == 'PUT':
                response = requests.put(full_url, json=body, headers=headers, timeout=self.command_timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(full_url, headers=headers, timeout=self.command_timeout)
            elif method.upper() == 'PATCH':
                response = requests.patch(full_url, json=body, headers=headers, timeout=self.command_timeout)
            elif method.upper() == 'HEAD':
                response = requests.head(full_url, headers=headers, timeout=self.command_timeout)
            elif method.upper() == 'OPTIONS':
                response = requests.options(full_url, headers=headers, timeout=self.command_timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            is_file_endpoint = url.endswith('/get_file') or 'get_file' in url
            if is_file_endpoint and isinstance(response_data, dict) and 'content' in response_data:
                self.handle_large_file_response(command_id, response_data)
            else:
                self.send_standard_response(command_id, response_data)
            
        except requests.exceptions.Timeout:
            print(f"API request timeout for command {command_id}")
            if self.sio.connected:
                try:
                    self.sio.emit('command_response', {
                        'command_id': command_id,
                        'response': {'error': 'API request timeout'}
                    })
                except Exception as emit_error:
                    print(f"Failed to emit timeout error: {emit_error}")
            
        except requests.exceptions.ConnectionError:
            print(f"API connection error for command {command_id}")
            if self.sio.connected:
                try:
                    self.sio.emit('command_response', {
                        'command_id': command_id,
                        'response': {'error': 'Failed to connect to local API server'}
                    })
                except Exception as emit_error:
                    print(f"Failed to emit connection error: {emit_error}")
            
        except Exception as e:
            print(f"General error for command {command_id}: {e}")
            if self.sio.connected:
                try:
                    self.sio.emit('command_response', {
                        'command_id': command_id,
                        'response': {'error': str(e)}
                    })
                except Exception as emit_error:
                    print(f"Failed to emit general error: {emit_error}")

    def send_standard_response(self, command_id, response_data):
        if self.sio.connected:
            try:
                self.sio.emit('command_response', {
                    'command_id': command_id,
                    'response': response_data
                })
                print(f"Successfully emitted response for command {command_id}")
                time.sleep(0.1)
            except Exception as emit_error:
                print(f"Failed to emit response: {emit_error}")
        else:
            print("Socket not connected, cannot emit response")

    def handle_large_file_response(self, command_id, response_data):
        import base64

        if 'content' not in response_data:
            self.send_standard_response(command_id, response_data)
            return

        content = response_data['content']

        if response_data.get('type') == 'binary':
            content_size = len(content) * 3 // 4
        else:
            content_size = len(content.encode('utf-8'))

        chunk_threshold = 4 * 1024 * 1024

        if content_size > chunk_threshold:
            print(f"File content size ({content_size} bytes) exceeds threshold, chunking...")
            self.send_chunked_file_response(command_id, response_data)
        else:
            print(f"File content size ({content_size} bytes) within limit, sending normally")
            self.send_standard_response(command_id, response_data)

    def send_chunked_file_response(self, command_id, response_data):
        import base64

        content = response_data['content']
        file_type = response_data.get('type', 'text')
        status = response_data.get('status', 'File content retrieved')

        chunk_size = 3 * 1024 * 1024

        if file_type == 'binary':
            try:
                original_bytes = base64.b64decode(content)
                total_size = len(original_bytes)
                chunks_needed = (total_size + chunk_size - 1) // chunk_size

                print(f"Sending binary file in {chunks_needed} chunks...")

                self.sio.emit('command_response', {
                    'command_id': command_id,
                    'response': {
                        'status': status,
                        'type': file_type,
                        'chunked': True,
                        'total_chunks': chunks_needed,
                        'total_size': total_size,
                        'chunk_index': 0
                    }
                })
                time.sleep(0.1)

                for i in range(chunks_needed):
                    start_pos = i * chunk_size
                    end_pos = min(start_pos + chunk_size, total_size)
                    chunk_bytes = original_bytes[start_pos:end_pos]
                    chunk_b64 = base64.b64encode(chunk_bytes).decode('utf-8')

                    self.sio.emit('command_response_chunk', {
                        'command_id': command_id,
                        'chunk_index': i,
                        'total_chunks': chunks_needed,
                        'content': chunk_b64,
                        'is_final': (i == chunks_needed - 1)
                    })
                    print(f"Sent chunk {i + 1}/{chunks_needed}")
                    time.sleep(0.05)

            except Exception as e:
                print(f"Error chunking binary content: {e}")
                self.send_standard_response(command_id, {'error': 'Failed to chunk binary content'})
        else:
            content_bytes = content.encode('utf-8')
            total_size = len(content_bytes)
            chunks_needed = (total_size + chunk_size - 1) // chunk_size

            print(f"Sending text file in {chunks_needed} chunks...")

            self.sio.emit('command_response', {
                'command_id': command_id,
                'response': {
                    'status': status,
                    'type': file_type,
                    'chunked': True,
                    'total_chunks': chunks_needed,
                    'total_size': total_size,
                    'chunk_index': 0
                }
            })
            time.sleep(0.1)

            for i in range(chunks_needed):
                start_pos = i * chunk_size
                end_pos = min(start_pos + chunk_size, total_size)
                chunk_bytes = content_bytes[start_pos:end_pos]
                chunk_text = chunk_bytes.decode('utf-8', errors='ignore')

                self.sio.emit('command_response_chunk', {
                    'command_id': command_id,
                    'chunk_index': i,
                    'total_chunks': chunks_needed,
                    'content': chunk_text,
                    'is_final': (i == chunks_needed - 1)
                })
                print(f"Sent chunk {i + 1}/{chunks_needed}")
                time.sleep(0.05)
    
def main():
    try:
        client = ShareifyLocalClient()
        
        print()
        print_status(f"\n=== Shareify Cloud Client Starting ===")
        print_status(f"Cloud URL: {client.cloud_url}")
        print_status(f"Server ID: {client.server_id}")
        print_status(f"Server Name: {client.server_name}")
        print_status(f"User ID: {client.user_id}")
        print_status(f"Username: {client.username}")
        print_status(f"Enabled: {client.enabled}")
        print_status(f"Heartbeat Interval: {client.heartbeat_interval}s")
        print_status(f"Command Timeout: {client.command_timeout}s")
        print_status("="*50)
        print()
        
        if not client.enabled:
            print_status("Cloud connection is disabled. Use 'shareify:enable' to enable it.", "warning")
            sys.exit(0)
        
        if client.connect():
            print_status("Client started successfully", "success")
            print("Waiting for commands from cloud...")
            client.wait()
        else:
            print_status("Failed to start client after all retry attempts", "error")
            print_status("This could be because:", "info")
            print_status("1. The cloud server is not running", "info")
            print_status("2. Network connectivity issues", "info")
            print_status("3. Incorrect cloud URL configuration", "info")
            print()
            sys.exit(1)
            
    except Exception as e:
        print_status(f"Unexpected error in main: {e}", "error")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
