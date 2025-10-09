import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))
try:
    import update
except ImportError:
    import update

def load_settings():
    settings_file = os.path.join(os.path.dirname(__file__), 'settings/settings.json')
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print('Error: Invalid JSON format in settings file.')
                return None
    else:
        print(f"Settings file '{settings_file}' not found.")
        return None
settings = load_settings()
try:
    from main import create_app
except ImportError:
    from main import create_app
application = create_app()
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    if settings:
        host = settings.get('host', '0.0.0.0')
        port = settings.get('port', 6969)
    else:
        host = '0.0.0.0'
        port = 6969
    update.kill_process_on_port(port)
    server = make_server(host, port, application)
    print(f'Server running on http://{host}:{port}')
    server.serve_forever()