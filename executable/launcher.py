import os
import json
import threading
from colorama import Fore

def is_cloud_on():
    try:
        cloud_path = os.path.join(os.path.dirname(__file__), 'settings', 'cloud.json')
        if os.path.exists(cloud_path):
            with open(cloud_path, 'r') as f:
                settings = json.load(f)
                return settings.get('enabled', '') == 'true'
    except Exception:
        pass
    return False

def start_cloud_connection():
    try:
        import cloud_connection
        cloud_connection.main()
    except Exception as e:
        print(f'Error starting cloud connection: {e}')

def start_wsgi_server():
    try:
        import wsgi
        if hasattr(wsgi, 'application'):
            from wsgiref.simple_server import make_server
            settings = wsgi.load_settings()
            if settings:
                host = settings.get('host', '0.0.0.0')
                port = settings.get('port', 8000)
            else:
                host = '0.0.0.0'
                port = 8000
            server = make_server(host, port, wsgi.application)
            print(f'Server running on http://{host}:{port}')
            server.serve_forever()
    except Exception as e:
        print(f'Error starting WSGI server: {e}')

def main():
    print("\n __ _                     __       \n/ _\\ |__   __ _ _ __ ___ / _|_   _ \n\\ \\| '_ \\ / _` | '__/ _ \\ |_| | | |\n_\\ \\ | | | (_| | | |  __/  _| |_| |\n\\__/_| |_|\\__,_|_|  \\___|_|  \\__, |\n                             |___/ \n")
    print("[Shareify] Starting Shareify..."+ Fore.RESET)
    threads = []
    
    wsgi_thread = threading.Thread(target=start_wsgi_server, daemon=True)
    wsgi_thread.start()
    threads.append(wsgi_thread)
    print("[Shareify] WSGI server started" + Fore.GREEN)    
    
    if is_cloud_on():
        cloud_thread = threading.Thread(target=start_cloud_connection, daemon=True)
        cloud_thread.start()
        threads.append(cloud_thread)
        print("[Shareify] Cloud connection started" + Fore.GREEN)

    print("[Shareify] Shareify startup complete" + Fore.GREEN)
    print(Fore.RESET)

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print('Shutting down...')

if __name__ == '__main__':
    main()