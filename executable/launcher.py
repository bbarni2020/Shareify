import os
import json
import threading
import sys
import errno
from pathlib import Path
from colorama import Fore
try:
    import update
except Exception:
    update = None

def is_admin():
    try:
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except Exception:
        return False

def relaunch_as_admin():
    if os.name == 'nt':
        import ctypes
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, params, None, 1)
        sys.exit(0)
    else:
        os.execvp('sudo', ['sudo', sys.executable, os.path.abspath(__file__)])

def is_cloud_on():
    try:
        cloud_path = os.path.join(os.path.dirname(__file__), 'settings', 'cloud.json')
        if os.path.exists(cloud_path):
            with open(cloud_path, 'r') as f:
                cfg = json.load(f)
                val = cfg.get('enabled', False)
                if isinstance(val, str):
                    return val.lower() == 'true'
                return bool(val)
    except Exception:
        pass
    return False

def _get_settings_port(default_port=8000):
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                data = json.load(f)
                return int(data.get('port', default_port))
    except Exception:
        pass
    return default_port

def _lockfile_path():
    port = _get_settings_port()
    tmp_dir = os.path.abspath(os.getenv('TMPDIR') or os.getenv('TMP') or '/tmp')
    return os.path.join(tmp_dir, f'shareify-{port}.pid')

def _already_running():
    pid_file = _lockfile_path()
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip() or '0')
            if pid > 0:
                try:
                    os.kill(pid, 0)
                    return True
                except OSError as e:
                    if e.errno == errno.ESRCH:
                        pass
                    else:
                        return True
    except Exception:
        pass
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
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
            try:
                if update and hasattr(update, 'kill_process_on_port'):
                    update.kill_process_on_port(port)
            except Exception:
                pass
            try:
                server = make_server(host, port, wsgi.application)
            except OSError as e:
                if 'Address already in use' in str(e) or getattr(e, 'errno', None) == 48:
                    try:
                        if update and hasattr(update, 'kill_process_on_port'):
                            update.kill_process_on_port(port)
                    except Exception:
                        pass
                    server = make_server(host, port, wsgi.application)
                else:
                    raise
            print(f'Server running on http://{host}:{port}')
            server.serve_forever()
    except Exception as e:
        print(f'Error starting WSGI server: {e}')

def main():
    if os.name == 'nt':
        os.system('title Shareify Server 1.2.0')
    else:
        print('\033]0;Shareify Server 1.2.0\007', end='')
    print("\n __ _                     __       \n/ _\\ |__   __ _ _ __ ___ / _|_   _ \n\\ \\| '_ \\ / _` | '__/ _ \\ |_| | | |\n_\\ \\ | | | (_| | | |  __/  _| |_| |\n\\__/_| |_|\\__,_|_|  \\___|_|  \\__, |\n                             |___/ \n")
    print("[Shareify] Starting Shareify..."+ Fore.RESET)
    if not is_admin():
        relaunch_as_admin()
    if _already_running():
        print("[Shareify] Another instance is already running" + Fore.GREEN)
        return
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