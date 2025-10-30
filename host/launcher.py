import os
import json
import threading
import sys
import errno
import multiprocessing
from pathlib import Path
from colorama import Fore
import time
import psutil
import socket
import subprocess
import curses
from datetime import datetime

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
        os.execvp('sudo', ['sudo', sys.executable] + sys.argv)

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

def get_tui_password():
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                data = json.load(f)
                return data.get('tui_password')
    except Exception:
        pass
    return None

def set_tui_password(password):
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings', 'settings.json')
        data = {}
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                data = json.load(f)
        
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        data['tui_password'] = password_hash
        
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

def verify_tui_password(password):
    stored_hash = get_tui_password()
    if not stored_hash:
        return False
    
    import hashlib
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return password_hash == stored_hash

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
    return os.path.join(tmp_dir, f'shareify-admin-{port}.pid')

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
        print(f'Error starting cloud connection: {e}', flush=True)

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
            print(f'Server running on http://{host}:{port}', flush=True)
            server.serve_forever()
    except Exception as e:
        print(f'Error starting WSGI server: {e}', flush=True)

class ServerManager:
    def __init__(self):
        self.wsgi_thread = None
        self.cloud_thread = None
        self.wsgi_running = False
        self.cloud_running = False
        
    def start_wsgi(self):
        if not self.wsgi_running:
            self.wsgi_thread = threading.Thread(target=start_wsgi_server, daemon=True)
            self.wsgi_thread.start()
            self.wsgi_running = True
            
    def stop_wsgi(self):
        if self.wsgi_running:
            try:
                settings_path = os.path.join(os.path.dirname(__file__), 'settings', 'settings.json')
                if os.path.exists(settings_path):
                    with open(settings_path, 'r') as f:
                        data = json.load(f)
                        port = int(data.get('port', 8000))
                else:
                    port = 8000
                if update and hasattr(update, 'kill_process_on_port'):
                    update.kill_process_on_port(port)
            except Exception:
                pass
            self.wsgi_running = False
            
    def start_cloud(self):
        if not self.cloud_running:
            self.cloud_thread = threading.Thread(target=start_cloud_connection, daemon=True)
            self.cloud_thread.start()
            self.cloud_running = True
            
    def stop_cloud(self):
        if self.cloud_running:
            self.cloud_running = False
            
    def get_status(self):
        return {
            'wsgi': self.wsgi_running,
            'cloud': self.cloud_running
        }

def get_network_status():
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', '2', 'google.com'], 
                              capture_output=True, timeout=3)
        if result.returncode == 0:
            return "Online"
        else:
            return "Offline"
    except Exception:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return "Online"
        except:
            return "Offline"

def get_ftp_status():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 21))
        sock.close()
        return "Running" if result == 0 else "Stopped"
    except:
        return "Stopped"

def get_shareify_server_status():
    try:
        settings_path = os.path.join(os.path.dirname(__file__), 'settings', 'settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                data = json.load(f)
                port = int(data.get('port', 8000))
        else:
            port = 8000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return "Running" if result == 0 else "Stopped"
    except:
        return "Stopped"

def get_wifi_interface():
    try:
        if sys.platform == 'darwin':
            result = subprocess.run(['networksetup', '-listallhardwareports'], 
                                  capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'Wi-Fi' in line and i + 1 < len(lines):
                    device_line = lines[i + 1]
                    if 'Device:' in device_line:
                        return device_line.split('Device:')[1].strip()
            return 'en0'
    except Exception:
        return 'en0'

def get_current_wifi():
    try:
        if sys.platform.startswith('linux'):
            result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], 
                                  capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if line.startswith('yes:'):
                    ssid = line.split('yes:')[1].strip()
                    if ssid:
                        return ssid
            
            result = subprocess.run(['iwgetid', '-r'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
    except Exception:
        pass
    return None

def get_wifi_signal_strength():
    try:
        if sys.platform.startswith('linux'):
            result = subprocess.run(['nmcli', '-t', '-f', 'active,signal', 'dev', 'wifi'], 
                                  capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if line.startswith('yes:'):
                    signal = line.split('yes:')[1].strip()
                    if signal:
                        return f"{signal}%"
            
            result = subprocess.run(['cat', '/proc/net/wireless'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                if len(lines) > 2:
                    parts = lines[2].split()
                    if len(parts) > 3:
                        quality = parts[2].rstrip('.')
                        return f"{quality}"
    except Exception:
        pass
    return "N/A"

def get_wifi_networks():
    networks = []
    try:
        if sys.platform.startswith('linux'):
            result = subprocess.run(['nmcli', '-t', '-f', 'SSID', 'dev', 'wifi', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                seen = set()
                for line in result.stdout.strip().split('\n'):
                    ssid = line.strip()
                    if ssid and ssid not in seen and ssid != '--':
                        networks.append(ssid)
                        seen.add(ssid)
            else:
                result = subprocess.run(['iwlist', 'scan'], 
                                      capture_output=True, text=True, timeout=10)
                for line in result.stdout.split('\n'):
                    if 'ESSID:' in line:
                        ssid = line.split('ESSID:')[1].strip().strip('"')
                        if ssid and ssid not in networks:
                            networks.append(ssid)
    except Exception:
        pass
    return networks

def connect_to_wifi(ssid, password):
    try:
        if sys.platform == 'darwin':
            subprocess.run(['networksetup', '-setairportnetwork', 'en0', ssid, password], 
                         capture_output=True, timeout=10)
            return True
        elif sys.platform.startswith('linux'):
            subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password], 
                         capture_output=True, timeout=10)
            return True
        elif sys.platform == 'win32':
            subprocess.run(['netsh', 'wlan', 'connect', f'name={ssid}'], 
                         capture_output=True, timeout=10)
            return True
    except Exception:
        return False
    return False

def draw_box(stdscr, y, x, height, width, title="", color=6):
    try:
        for i in range(height):
            if i == 0:
                stdscr.addstr(y + i, x, "╭" + "─" * (width - 2) + "╮", curses.color_pair(color))
            elif i == height - 1:
                stdscr.addstr(y + i, x, "╰" + "─" * (width - 2) + "╯", curses.color_pair(color))
            else:
                stdscr.addstr(y + i, x, "│" + " " * (width - 2) + "│", curses.color_pair(color))
        
        if title:
            title_text = f" {title} "
            title_x = x + (width - len(title_text)) // 2
            stdscr.addstr(y, title_x, title_text, curses.color_pair(color) | curses.A_BOLD)
    except:
        pass

def draw_button(stdscr, y, x, text, selected=False, color=4):
    try:
        if selected:
            stdscr.addstr(y, x, "▶ ", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(y, x + 2, text, curses.color_pair(color) | curses.A_BOLD | curses.A_REVERSE)
        else:
            stdscr.addstr(y, x, "  " + text, curses.color_pair(color))
    except:
        pass

def draw_status_indicator(stdscr, y, x, label, status, is_active):
    try:
        stdscr.addstr(y, x, "●", curses.color_pair(1 if is_active else 2) | curses.A_BOLD)
        stdscr.addstr(y, x + 2, label, curses.color_pair(4))
        stdscr.addstr(y, x + 25, status, curses.color_pair(1 if is_active else 2) | curses.A_BOLD)
    except:
        pass

def draw_ascii_art(stdscr, start_y, start_x):
    ascii_lines = [
        " __ _                     __       ",
        "/ _\\ |__   __ _ _ __ ___ / _|_   _ ",
        "\\ \\| '_ \\ / _` | '__/ _ \\ |_| | | |",
        "_\\ \\ | | | (_| | | |  __/  _| |_| |",
        "\\__/_| |_|\\__,_|_|  \\___|_|  \\__, |",
        "                             |___/ "
    ]
    
    for i, line in enumerate(ascii_lines):
        try:
            stdscr.addstr(start_y + i, start_x, line, curses.color_pair(5) | curses.A_BOLD)
        except:
            pass

def show_login_screen(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(0)
    
    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_WHITE, -1)
    except:
        pass
    
    stored_password = get_tui_password()
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if height < 20 or width < 70:
            stdscr.addstr(0, 0, "Terminal too small! Resize to at least 70x20", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(0.5)
            continue
        
        draw_ascii_art(stdscr, 2, (width - 36) // 2)
        
        title_line = "━" * (width - 4)
        stdscr.addstr(1, 2, title_line, curses.color_pair(5))
        stdscr.addstr(8, 2, title_line, curses.color_pair(5))
        
        box_width = 50
        box_height = 12
        box_x = (width - box_width) // 2
        box_y = 10
        
        if not stored_password:
            draw_box(stdscr, box_y, box_x, box_height, box_width, "Setup Password", 4)
            
            stdscr.addstr(box_y + 2, box_x + 4, "First time setup", curses.color_pair(3) | curses.A_BOLD)
            stdscr.addstr(box_y + 3, box_x + 4, "Create a password to access TUI", curses.color_pair(6))
            
            stdscr.addstr(box_y + 5, box_x + 4, "New Password:", curses.color_pair(4))
            stdscr.addstr(box_y + 7, box_x + 4, "Confirm Password:", curses.color_pair(4))
            
            stdscr.refresh()
            
            curses.echo()
            curses.noecho()
            
            password1 = ""
            password2 = ""
            
            stdscr.addstr(box_y + 5, box_x + 20, " " * 20, curses.color_pair(6))
            stdscr.move(box_y + 5, box_x + 20)
            stdscr.refresh()
            
            while True:
                ch = stdscr.getch()
                if ch == ord('\n'):
                    break
                elif ch == 127 or ch == curses.KEY_BACKSPACE:
                    if password1:
                        password1 = password1[:-1]
                        y, x = stdscr.getyx()
                        stdscr.addstr(y, box_x + 20, " " * 20, curses.color_pair(6))
                        stdscr.addstr(y, box_x + 20, "*" * len(password1), curses.color_pair(6))
                elif 32 <= ch <= 126:
                    password1 += chr(ch)
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 20, "*" * len(password1), curses.color_pair(6))
                stdscr.refresh()
            
            stdscr.addstr(box_y + 7, box_x + 20, " " * 20, curses.color_pair(6))
            stdscr.move(box_y + 7, box_x + 20)
            stdscr.refresh()
            
            while True:
                ch = stdscr.getch()
                if ch == ord('\n'):
                    break
                elif ch == 127 or ch == curses.KEY_BACKSPACE:
                    if password2:
                        password2 = password2[:-1]
                        y, x = stdscr.getyx()
                        stdscr.addstr(y, box_x + 20, " " * 20, curses.color_pair(6))
                        stdscr.addstr(y, box_x + 20, "*" * len(password2), curses.color_pair(6))
                elif 32 <= ch <= 126:
                    password2 += chr(ch)
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 20, "*" * len(password2), curses.color_pair(6))
                stdscr.refresh()
            
            if not password1 or not password2:
                stdscr.addstr(box_y + 9, box_x + 4, "Password cannot be empty!", curses.color_pair(2) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(2)
                continue
            
            if password1 != password2:
                stdscr.addstr(box_y + 9, box_x + 4, "Passwords do not match!", curses.color_pair(2) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(2)
                continue
            
            if set_tui_password(password1):
                stdscr.addstr(box_y + 9, box_x + 4, "Password set successfully!", curses.color_pair(1) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(1)
                return True
            else:
                stdscr.addstr(box_y + 9, box_x + 4, "Failed to save password!", curses.color_pair(2) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(2)
                continue
        else:
            draw_box(stdscr, box_y, box_x, 8, box_width, "Login", 4)
            
            stdscr.addstr(box_y + 2, box_x + 4, "Enter Password:", curses.color_pair(4))
            stdscr.addstr(box_y + 5, box_x + 4, "Press ESC to exit", curses.color_pair(7))
            
            stdscr.addstr(box_y + 2, box_x + 20, " " * 20, curses.color_pair(6))
            stdscr.move(box_y + 2, box_x + 20)
            stdscr.refresh()
            
            password = ""
            
            while True:
                ch = stdscr.getch()
                if ch == ord('\n'):
                    break
                elif ch == 27:
                    return False
                elif ch == 127 or ch == curses.KEY_BACKSPACE:
                    if password:
                        password = password[:-1]
                        y, x = stdscr.getyx()
                        stdscr.addstr(y, box_x + 20, " " * 20, curses.color_pair(6))
                        stdscr.addstr(y, box_x + 20, "*" * len(password), curses.color_pair(6))
                elif 32 <= ch <= 126:
                    password += chr(ch)
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 20, "*" * len(password), curses.color_pair(6))
                stdscr.refresh()
            
            if verify_tui_password(password):
                stdscr.addstr(box_y + 4, box_x + 4, "Login successful!", curses.color_pair(1) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(1)
                return True
            else:
                stdscr.addstr(box_y + 4, box_x + 4, "Incorrect password!", curses.color_pair(2) | curses.A_BOLD)
                stdscr.refresh()
                time.sleep(2)

def change_password_screen(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(0)
    
    height, width = stdscr.getmaxyx()
    
    box_width = 60
    box_height = 12
    box_x = (width - box_width) // 2
    box_y = (height - box_height) // 2
    
    while True:
        stdscr.clear()
        draw_box(stdscr, box_y, box_x, box_height, box_width, "Change Password", 3)
        
        stdscr.addstr(box_y + 2, box_x + 4, "Current Password:", curses.color_pair(4))
        stdscr.addstr(box_y + 4, box_x + 4, "New Password:", curses.color_pair(4))
        stdscr.addstr(box_y + 6, box_x + 4, "Confirm New:", curses.color_pair(4))
        stdscr.addstr(box_y + 9, box_x + 4, "ESC to cancel", curses.color_pair(7))
        
        stdscr.refresh()
        
        current_pass = ""
        new_pass = ""
        confirm_pass = ""
        
        stdscr.addstr(box_y + 2, box_x + 23, " " * 30, curses.color_pair(6))
        stdscr.move(box_y + 2, box_x + 23)
        stdscr.refresh()
        
        while True:
            ch = stdscr.getch()
            if ch == ord('\n'):
                break
            elif ch == 27:
                return False
            elif ch == 127 or ch == curses.KEY_BACKSPACE:
                if current_pass:
                    current_pass = current_pass[:-1]
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 23, " " * 30, curses.color_pair(6))
                    stdscr.addstr(y, box_x + 23, "*" * len(current_pass), curses.color_pair(6))
            elif 32 <= ch <= 126:
                if len(current_pass) < 30:
                    current_pass += chr(ch)
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 23, "*" * len(current_pass), curses.color_pair(6))
            stdscr.refresh()
        
        if not verify_tui_password(current_pass):
            stdscr.addstr(box_y + 8, box_x + 4, "✗ Current password incorrect!", curses.color_pair(2) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(2)
            continue
        
        stdscr.addstr(box_y + 4, box_x + 23, " " * 30, curses.color_pair(6))
        stdscr.move(box_y + 4, box_x + 23)
        stdscr.refresh()
        
        while True:
            ch = stdscr.getch()
            if ch == ord('\n'):
                break
            elif ch == 27:
                return False
            elif ch == 127 or ch == curses.KEY_BACKSPACE:
                if new_pass:
                    new_pass = new_pass[:-1]
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 23, " " * 30, curses.color_pair(6))
                    stdscr.addstr(y, box_x + 23, "*" * len(new_pass), curses.color_pair(6))
            elif 32 <= ch <= 126:
                if len(new_pass) < 30:
                    new_pass += chr(ch)
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 23, "*" * len(new_pass), curses.color_pair(6))
            stdscr.refresh()
        
        stdscr.addstr(box_y + 6, box_x + 23, " " * 30, curses.color_pair(6))
        stdscr.move(box_y + 6, box_x + 23)
        stdscr.refresh()
        
        while True:
            ch = stdscr.getch()
            if ch == ord('\n'):
                break
            elif ch == 27:
                return False
            elif ch == 127 or ch == curses.KEY_BACKSPACE:
                if confirm_pass:
                    confirm_pass = confirm_pass[:-1]
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 23, " " * 30, curses.color_pair(6))
                    stdscr.addstr(y, box_x + 23, "*" * len(confirm_pass), curses.color_pair(6))
            elif 32 <= ch <= 126:
                if len(confirm_pass) < 30:
                    confirm_pass += chr(ch)
                    y, x = stdscr.getyx()
                    stdscr.addstr(y, box_x + 23, "*" * len(confirm_pass), curses.color_pair(6))
            stdscr.refresh()
        
        if not new_pass or not confirm_pass:
            stdscr.addstr(box_y + 8, box_x + 4, "✗ Password cannot be empty!", curses.color_pair(2) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(2)
            continue
        
        if new_pass != confirm_pass:
            stdscr.addstr(box_y + 8, box_x + 4, "✗ Passwords don't match!", curses.color_pair(2) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(2)
            continue
        
        if set_tui_password(new_pass):
            stdscr.addstr(box_y + 8, box_x + 4, "✓ Password changed successfully!", curses.color_pair(1) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(2)
            return True
        else:
            stdscr.addstr(box_y + 8, box_x + 4, "✗ Failed to save password!", curses.color_pair(2) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(2)
            return False

def run_terminal_mode(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(0)
    
    height, width = stdscr.getmaxyx()
    
    term_history = []
    scroll_offset = 0
    current_dir = os.path.dirname(__file__)
    
    import getpass
    username = getpass.getuser()
    hostname = socket.gethostname()
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        if height < 10 or width < 60:
            stdscr.addstr(0, 0, "Terminal too small! Resize to at least 60x10", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(0.5)
            continue
        
        draw_box(stdscr, 0, 0, height - 1, width, "Terminal Session", 5)
        
        help_text = "Type 'exit' to quit  •  'clear' to clear history"
        try:
            stdscr.addstr(1, (width - len(help_text)) // 2, help_text, curses.color_pair(7))
        except:
            pass
        
        display_height = height - 6
        visible_history = term_history[max(0, len(term_history) - display_height):]
        
        start_y = 2
        for idx, line in enumerate(visible_history):
            if start_y + idx < height - 3:
                display_line = line[:width - 4]
                try:
                    if line.startswith(f"{username}@"):
                        parts = line.split('$ ', 1)
                        if len(parts) == 2:
                            stdscr.addstr(start_y + idx, 2, parts[0] + '$ ', curses.color_pair(1) | curses.A_BOLD)
                            stdscr.addstr(start_y + idx, 2 + len(parts[0]) + 2, parts[1], curses.color_pair(6))
                        else:
                            stdscr.addstr(start_y + idx, 2, display_line, curses.color_pair(6))
                    elif line.startswith("ERROR:") or line.startswith("✗"):
                        stdscr.addstr(start_y + idx, 2, display_line, curses.color_pair(2))
                    elif line.startswith("✓"):
                        stdscr.addstr(start_y + idx, 2, display_line, curses.color_pair(1))
                    else:
                        stdscr.addstr(start_y + idx, 2, display_line, curses.color_pair(6))
                except:
                    pass
        
        prompt_y = height - 3
        
        try:
            stdscr.addstr(prompt_y, 2, "─" * (width - 4), curses.color_pair(7))
        except:
            pass
        
        prompt_y += 1
        
        dir_display = current_dir.replace(os.path.expanduser('~'), '~')
        if len(dir_display) > width - 20:
            dir_display = '...' + dir_display[-(width - 23):]
        
        prompt_str = f"{username}@{hostname}:{dir_display}$ "
        prompt_display = prompt_str
        if len(prompt_display) > width - 6:
            prompt_display = f"{username}@{hostname}:...$ "
        
        try:
            stdscr.addstr(prompt_y, 2, prompt_display, curses.color_pair(1) | curses.A_BOLD)
        except:
            pass
        
        input_start_x = 2 + len(prompt_display)
        max_input_width = width - input_start_x - 4
        
        stdscr.refresh()
        stdscr.move(prompt_y, input_start_x)
        
        curses.echo()
        try:
            user_input = stdscr.getstr(prompt_y, input_start_x, max_input_width).decode('utf-8').strip()
        except:
            curses.noecho()
            continue
        curses.noecho()
        
        if user_input.lower() == 'exit':
            break
        
        if user_input.lower() == 'clear':
            term_history = []
            continue
        
        if user_input:
            term_history.append(f"{username}@{hostname}:{dir_display}$ {user_input}")
            
            if user_input.startswith('cd '):
                target_dir = user_input[3:].strip()
                if target_dir == '~':
                    target_dir = os.path.expanduser('~')
                elif target_dir.startswith('~/'):
                    target_dir = os.path.expanduser(target_dir)
                elif not os.path.isabs(target_dir):
                    target_dir = os.path.join(current_dir, target_dir)
                
                try:
                    target_dir = os.path.abspath(target_dir)
                    if os.path.isdir(target_dir):
                        current_dir = target_dir
                        term_history.append(f"✓ Changed directory to {current_dir.replace(os.path.expanduser('~'), '~')}")
                    else:
                        term_history.append(f"✗ ERROR: Directory not found: {target_dir}")
                except Exception as e:
                    term_history.append(f"✗ ERROR: {str(e)}")
            else:
                try:
                    result = subprocess.run(
                        user_input,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        cwd=current_dir
                    )
                    
                    output_lines = []
                    if result.stdout:
                        output_lines.extend(result.stdout.rstrip('\n').split('\n'))
                    
                    if result.stderr:
                        for line in result.stderr.rstrip('\n').split('\n'):
                            if line:
                                output_lines.append(f"ERROR: {line}")
                    
                    if not output_lines and result.returncode == 0:
                        pass
                    elif result.returncode != 0 and not result.stderr:
                        output_lines.append(f"✗ Command exited with code {result.returncode}")
                    
                    for line in output_lines:
                        if line:
                            term_history.append(line)
                        
                except subprocess.TimeoutExpired:
                    term_history.append("✗ ERROR: Command timed out (30s limit)")
                except Exception as e:
                    term_history.append(f"✗ ERROR: {str(e)}")
    
    curses.curs_set(0)

def run_tui_mode(skip_instance_check=False, server_manager=None, from_os_mode=False):
    def tui_main(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(1)
        stdscr.timeout(100)
        
        try:
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_RED, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_CYAN, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_WHITE, -1)
            curses.init_pair(7, 240, -1)
        except:
            pass
        
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except:
            pass
        
        nonlocal server_manager
        if server_manager is None:
            server_manager = ServerManager()
        
        selected_option = 0
        
        if from_os_mode:
            if sys.platform.startswith('linux'):
                menu_items = [
                    "Toggle Shareify Server",
                    "Toggle Cloud Connection",
                    "WiFi Networks",
                    "Terminal",
                    "Change Password",
                    "Logout"
                ]
            else:
                menu_items = [
                    "Toggle Shareify Server",
                    "Toggle Cloud Connection",
                    "Terminal",
                    "Change Password",
                    "Logout"
                ]
        else:
            if sys.platform.startswith('linux'):
                menu_items = [
                    "Toggle Shareify Server",
                    "Toggle Cloud Connection",
                    "WiFi Networks",
                    "Terminal",
                    "Change Password"
                ]
            else:
                menu_items = [
                    "Toggle Shareify Server",
                    "Toggle Cloud Connection",
                    "Terminal",
                    "Change Password"
                ]
        
        last_status_check = 0
        last_resource_check = 0
        status_cache = {'wsgi': False, 'cloud': False}
        resource_cache = {'cpu': 0, 'mem': 0, 'disk': 0, 'disk_used': 0, 'disk_total': 0}
        
        if not skip_instance_check and _already_running():
            stdscr.addstr(0, 0, "Another instance is already running", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(2)
            return None, None
        
        if not skip_instance_check:
            server_manager.start_wsgi()
            if is_cloud_on():
                server_manager.start_cloud()
        
        wifi_networks = []
        wifi_selected = 0
        wifi_mode = False
        message = ""
        message_time = 0
        
        while True:
            try:
                stdscr.clear()
                height, width = stdscr.getmaxyx()
                
                current_time_check = time.time()
                if current_time_check - last_status_check > 0.5:
                    status_cache = server_manager.get_status()
                    last_status_check = current_time_check
                
                if height < 35 or width < 120:
                    stdscr.addstr(0, 0, "Terminal too small! Resize to at least 120x35", curses.color_pair(2))
                    stdscr.refresh()
                    key = stdscr.getch()
                    if key == ord('q') or key == ord('Q'):
                        break
                    continue
                
                header_y = 1
                stdscr.addstr(header_y, (width - 36) // 2, " __ _                     __       ", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(header_y + 1, (width - 36) // 2, "/ _\\ |__   __ _ _ __ ___ / _|_   _ ", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(header_y + 2, (width - 36) // 2, "\\ \\| '_ \\ / _` | '__/ _ \\ |_| | | |", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(header_y + 3, (width - 36) // 2, "_\\ \\ | | | (_| | | |  __/  _| |_| |", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(header_y + 4, (width - 36) // 2, "\\__/_| |_|\\__,_|_|  \\___|_|  \\__, |", curses.color_pair(5) | curses.A_BOLD)
                stdscr.addstr(header_y + 5, (width - 36) // 2, "                             |___/ ", curses.color_pair(5) | curses.A_BOLD)
                
                divider_y = 8
                stdscr.addstr(divider_y, 2, "═" * (width - 4), curses.color_pair(7))
                
                main_content_y = 10
                
                left_col_x = 3
                left_col_width = width // 3 - 3
                
                draw_box(stdscr, main_content_y, left_col_x, 14, left_col_width, "System Status", 4)
                
                cloud_status = "Running" if status_cache['cloud'] else "Stopped"
                cloud_active = status_cache['cloud']
                
                ftp_status = get_ftp_status()
                ftp_active = ftp_status == "Running"
                
                shareify_status = "Running" if status_cache['wsgi'] else "Stopped"
                shareify_active = status_cache['wsgi']
                
                network_status = get_network_status()
                network_active = network_status == "Online"
                
                current_time = datetime.now().strftime("%H:%M:%S")
                current_date = datetime.now().strftime("%Y-%m-%d")
                
                draw_status_indicator(stdscr, main_content_y + 2, left_col_x + 2, "Shareify", shareify_status, shareify_active)
                draw_status_indicator(stdscr, main_content_y + 4, left_col_x + 2, "Cloud", cloud_status, cloud_active)
                draw_status_indicator(stdscr, main_content_y + 6, left_col_x + 2, "FTP", ftp_status, ftp_active)
                draw_status_indicator(stdscr, main_content_y + 8, left_col_x + 2, "Network", network_status, network_active)
                
                stdscr.addstr(main_content_y + 11, left_col_x + 2, "⏰", curses.color_pair(3))
                stdscr.addstr(main_content_y + 11, left_col_x + 5, current_time, curses.color_pair(6) | curses.A_BOLD)
                stdscr.addstr(main_content_y + 11, left_col_x + 15, current_date, curses.color_pair(7))
                
                mid_col_x = width // 3 + 1
                mid_col_width = width // 3 - 2
                
                if not wifi_mode:
                    draw_box(stdscr, main_content_y, mid_col_x, 14, mid_col_width, "Controls", 3)
                    
                    for idx, item in enumerate(menu_items):
                        item_y = main_content_y + 2 + idx * 2
                        if item_y < main_content_y + 12:
                            draw_button(stdscr, item_y, mid_col_x + 3, item, idx == selected_option, 4)
                else:
                    if sys.platform.startswith('linux'):
                        draw_box(stdscr, main_content_y, mid_col_x, 24, mid_col_width, "WiFi Networks", 3)
                        
                        current_wifi = get_current_wifi()
                        wifi_strength = get_wifi_signal_strength()
                        
                        if current_wifi:
                            stdscr.addstr(main_content_y + 2, mid_col_x + 3, "● ", curses.color_pair(1) | curses.A_BOLD)
                            stdscr.addstr(main_content_y + 2, mid_col_x + 5, "Connected:", curses.color_pair(4))
                            conn_text = current_wifi[:mid_col_width - 20]
                            stdscr.addstr(main_content_y + 2, mid_col_x + 17, conn_text, curses.color_pair(1) | curses.A_BOLD)
                            
                            stdscr.addstr(main_content_y + 3, mid_col_x + 5, "Signal:", curses.color_pair(4))
                            stdscr.addstr(main_content_y + 3, mid_col_x + 17, wifi_strength, curses.color_pair(3))
                            
                            stdscr.addstr(main_content_y + 4, mid_col_x + 3, "─" * (mid_col_width - 6), curses.color_pair(7))
                            
                            net_start_y = main_content_y + 5
                        else:
                            stdscr.addstr(main_content_y + 2, mid_col_x + 3, "○ ", curses.color_pair(2))
                            stdscr.addstr(main_content_y + 2, mid_col_x + 5, "Not connected", curses.color_pair(2))
                            stdscr.addstr(main_content_y + 3, mid_col_x + 3, "─" * (mid_col_width - 6), curses.color_pair(7))
                            net_start_y = main_content_y + 4
                    else:
                        wifi_mode = False
                        continue
                    
                    if not wifi_networks:
                        stdscr.addstr(net_start_y, mid_col_x + 3, "⟳ Scanning...", curses.color_pair(3) | curses.A_BOLD)
                    else:
                        stdscr.addstr(net_start_y, mid_col_x + 3, "Available:", curses.color_pair(6))
                        for idx, net in enumerate(wifi_networks[:8]):
                            item_y = net_start_y + 1 + idx * 2
                            if item_y < main_content_y + 22:
                                is_current = (net == current_wifi)
                                net_display = net[:mid_col_width - 10]
                                if idx == wifi_selected:
                                    stdscr.addstr(item_y, mid_col_x + 3, "▶ ", curses.color_pair(3) | curses.A_BOLD)
                                    if is_current:
                                        stdscr.addstr(item_y, mid_col_x + 5, net_display + " ✓", curses.color_pair(1) | curses.A_REVERSE | curses.A_BOLD)
                                    else:
                                        stdscr.addstr(item_y, mid_col_x + 5, net_display, curses.color_pair(4) | curses.A_REVERSE | curses.A_BOLD)
                                else:
                                    if is_current:
                                        stdscr.addstr(item_y, mid_col_x + 3, "  " + net_display + " ✓", curses.color_pair(1))
                                    else:
                                        stdscr.addstr(item_y, mid_col_x + 3, "  " + net_display, curses.color_pair(6))
                
                right_col_x = (width // 3) * 2 + 1
                right_col_width = width - right_col_x - 3
                
                current_resource_check = time.time()
                if current_resource_check - last_resource_check > 2:
                    try:
                        resource_cache['cpu'] = psutil.cpu_percent(interval=0.1)
                        mem = psutil.virtual_memory()
                        resource_cache['mem'] = mem.percent
                        disk = psutil.disk_usage('/')
                        resource_cache['disk'] = disk.percent
                        resource_cache['disk_used'] = disk.used / (1024**3)
                        resource_cache['disk_total'] = disk.total / (1024**3)
                        last_resource_check = current_resource_check
                    except:
                        pass
                
                try:
                    draw_box(stdscr, main_content_y, right_col_x, 14, right_col_width, "Resources", 5)
                    
                    cpu_percent = resource_cache['cpu']
                    stdscr.addstr(main_content_y + 2, right_col_x + 2, "CPU", curses.color_pair(4))
                    cpu_bar_width = right_col_width - 12
                    cpu_fill = int((cpu_percent / 100) * cpu_bar_width)
                    cpu_color = 1 if cpu_percent < 60 else (3 if cpu_percent < 80 else 2)
                    stdscr.addstr(main_content_y + 3, right_col_x + 2, "[" + "█" * cpu_fill + " " * (cpu_bar_width - cpu_fill) + "]", curses.color_pair(cpu_color))
                    stdscr.addstr(main_content_y + 3, right_col_x + right_col_width - 6, f"{cpu_percent:5.1f}%", curses.color_pair(cpu_color) | curses.A_BOLD)
                    
                    mem_percent = resource_cache['mem']
                    stdscr.addstr(main_content_y + 5, right_col_x + 2, "RAM", curses.color_pair(4))
                    mem_bar_width = right_col_width - 12
                    mem_fill = int((mem_percent / 100) * mem_bar_width)
                    mem_color = 1 if mem_percent < 60 else (3 if mem_percent < 80 else 2)
                    stdscr.addstr(main_content_y + 6, right_col_x + 2, "[" + "█" * mem_fill + " " * (mem_bar_width - mem_fill) + "]", curses.color_pair(mem_color))
                    stdscr.addstr(main_content_y + 6, right_col_x + right_col_width - 6, f"{mem_percent:5.1f}%", curses.color_pair(mem_color) | curses.A_BOLD)
                    
                    disk_percent = resource_cache['disk']
                    stdscr.addstr(main_content_y + 8, right_col_x + 2, "DISK", curses.color_pair(4))
                    disk_bar_width = right_col_width - 12
                    disk_fill = int((disk_percent / 100) * disk_bar_width)
                    disk_color = 1 if disk_percent < 60 else (3 if disk_percent < 80 else 2)
                    stdscr.addstr(main_content_y + 9, right_col_x + 2, "[" + "█" * disk_fill + " " * (disk_bar_width - disk_fill) + "]", curses.color_pair(disk_color))
                    stdscr.addstr(main_content_y + 9, right_col_x + right_col_width - 6, f"{disk_percent:5.1f}%", curses.color_pair(disk_color) | curses.A_BOLD)
                    
                    gb_used = resource_cache['disk_used']
                    gb_total = resource_cache['disk_total']
                    stdscr.addstr(main_content_y + 11, right_col_x + 2, f"{gb_used:.1f}GB / {gb_total:.1f}GB", curses.color_pair(7))
                except:
                    draw_box(stdscr, main_content_y, right_col_x, 14, right_col_width, "Resources", 5)
                    stdscr.addstr(main_content_y + 2, right_col_x + 2, "Loading...", curses.color_pair(7))
                
                footer_y = height - 3
                stdscr.addstr(footer_y, 2, "═" * (width - 4), curses.color_pair(7))
                
                footer_text = "↑↓ Navigate  •  ↵ Select  •  Mouse Enabled  •  Ctrl+C Exit"
                stdscr.addstr(footer_y + 1, (width - len(footer_text)) // 2, footer_text, curses.color_pair(7))
                
                if message and time.time() - message_time < 3:
                    msg_y = height - 6
                    msg_box_width = len(message) + 4
                    msg_box_x = (width - msg_box_width) // 2
                    stdscr.addstr(msg_y - 1, msg_box_x, "╭" + "─" * (msg_box_width - 2) + "╮", curses.color_pair(1))
                    stdscr.addstr(msg_y, msg_box_x, "│ " + message + " │", curses.color_pair(1) | curses.A_BOLD)
                    stdscr.addstr(msg_y + 1, msg_box_x, "╰" + "─" * (msg_box_width - 2) + "╯", curses.color_pair(1))
                
                stdscr.refresh()
                
                key = stdscr.getch()
                
                if key == curses.KEY_MOUSE:
                    try:
                        _, mx, my, _, bstate = curses.getmouse()
                        if bstate & curses.BUTTON1_CLICKED:
                            if not wifi_mode:
                                for idx in range(len(menu_items)):
                                    item_y = main_content_y + 2 + idx * 2
                                    if my == item_y and mx >= mid_col_x + 3 and mx < mid_col_x + mid_col_width - 3:
                                        selected_option = idx
                                        key = ord('\n')
                                        break
                            else:
                                current_wifi = get_current_wifi()
                                net_start_y = main_content_y + 5 if current_wifi else main_content_y + 4
                                for idx in range(min(8, len(wifi_networks))):
                                    item_y = net_start_y + 1 + idx * 2
                                    if my == item_y and mx >= mid_col_x + 3 and mx < mid_col_x + mid_col_width - 3:
                                        wifi_selected = idx
                                        key = ord('\n')
                                        break
                    except:
                        pass
                
                if not wifi_mode:
                    if key == curses.KEY_UP and selected_option > 0:
                        selected_option -= 1
                    elif key == curses.KEY_DOWN and selected_option < len(menu_items) - 1:
                        selected_option += 1
                    elif key == ord('\n'):
                        if selected_option == 0:
                            if status_cache['wsgi']:
                                server_manager.stop_wsgi()
                                message = "✓ Shareify Server stopped"
                                status_cache['wsgi'] = False
                            else:
                                server_manager.start_wsgi()
                                message = "✓ Shareify Server started"
                                status_cache['wsgi'] = True
                            message_time = time.time()
                            time.sleep(0.5)
                        elif selected_option == 1:
                            if status_cache['cloud']:
                                server_manager.stop_cloud()
                                message = "✓ Cloud Connection stopped"
                                status_cache['cloud'] = False
                            else:
                                server_manager.start_cloud()
                                message = "✓ Cloud Connection started"
                                status_cache['cloud'] = True
                            message_time = time.time()
                            time.sleep(0.5)
                        elif selected_option == 2 and sys.platform.startswith('linux'):
                            wifi_mode = True
                            wifi_networks = get_wifi_networks()
                            wifi_selected = 0
                        elif (selected_option == 3 and sys.platform.startswith('linux')) or (selected_option == 2 and not sys.platform.startswith('linux')):
                            run_terminal_mode(stdscr)
                            stdscr.nodelay(1)
                            stdscr.timeout(100)
                        elif (selected_option == 4 and sys.platform.startswith('linux')) or (selected_option == 3 and not sys.platform.startswith('linux')):
                            change_password_screen(stdscr)
                            stdscr.nodelay(1)
                            stdscr.timeout(100)
                        elif (selected_option == 5 and sys.platform.startswith('linux')) or (selected_option == 4 and not sys.platform.startswith('linux')):
                            return True, server_manager
                else:
                    if key == curses.KEY_UP and wifi_selected > 0:
                        wifi_selected -= 1
                    elif key == curses.KEY_DOWN and wifi_selected < len(wifi_networks) - 1:
                        wifi_selected += 1
                    elif key == ord('\n') and wifi_networks:
                        curses.echo()
                        curses.curs_set(1)
                        stdscr.clear()
                        prompt_y = height // 2
                        prompt_x = (width - 60) // 2
                        
                        draw_box(stdscr, prompt_y - 2, prompt_x - 2, 5, 64, "Enter WiFi Password", 3)
                        stdscr.addstr(prompt_y, prompt_x, f"Network: {wifi_networks[wifi_selected]}", curses.color_pair(4) | curses.A_BOLD)
                        stdscr.addstr(prompt_y + 1, prompt_x, "Password: ", curses.color_pair(6))
                        stdscr.refresh()
                        
                        password = stdscr.getstr(prompt_y + 1, prompt_x + 10, 50).decode('utf-8')
                        curses.noecho()
                        curses.curs_set(0)
                        
                        if connect_to_wifi(wifi_networks[wifi_selected], password):
                            message = f"✓ Connected to {wifi_networks[wifi_selected]}"
                        else:
                            message = f"✗ Failed to connect to {wifi_networks[wifi_selected]}"
                        message_time = time.time()
                        wifi_mode = False
                    elif key == 27:
                        wifi_mode = False
                    
            except KeyboardInterrupt:
                break
            except Exception:
                pass
        
        return False, server_manager
    
    try:
        result = curses.wrapper(tui_main)
        if result is None:
            return False, None
        return result
    except Exception as e:
        print(f"TUI Error: {e}")
        sys.exit(1)

def main():
    if os.name == 'nt':
        os.system('title Shareify Server 1.2.0')
    else:
        print('\033]0;Shareify Server 1.2.0\007', end='')
    
    if not is_admin():
        relaunch_as_admin()
        return
    
    print("\n __ _                     __       \n/ _\\ |__   __ _ _ __ ___ / _|_   _ \n\\ \\| '_ \\ / _` | '__/ _ \\ |_| | | |\n_\\ \\ | | | (_| | | |  __/  _| |_| |\n\\__/_| |_|\\__,_|_|  \\___|_|  \\__, |\n                             |___/ \n", flush=True)
    print("[Shareify] Starting Shareify..."+ Fore.RESET, flush=True)
    
    if _already_running():
        print("[Shareify] Another instance is already running" + Fore.GREEN, flush=True)
        sys.exit(0)
    threads = []
    
    wsgi_thread = threading.Thread(target=start_wsgi_server, daemon=True)
    wsgi_thread.start()
    threads.append(wsgi_thread)
    print("[Shareify] WSGI server started" + Fore.GREEN, flush=True)    
    
    if is_cloud_on():
        cloud_thread = threading.Thread(target=start_cloud_connection, daemon=True)
        cloud_thread.start()
        threads.append(cloud_thread)
        print("[Shareify] Cloud connection started" + Fore.GREEN, flush=True)

    print("[Shareify] Shareify startup complete" + Fore.GREEN, flush=True)
    print(Fore.RESET, flush=True)

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print('Shutting down...', flush=True)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == 'tui':
            run_tui_mode()
        elif mode == 'os':
            try:
                first_run = True
                shared_server_manager = None
                while True:
                    def login_wrapper(stdscr):
                        if show_login_screen(stdscr):
                            return True
                        return False
                    
                    login_success = curses.wrapper(login_wrapper)
                    
                    if not login_success:
                        if shared_server_manager:
                            shared_server_manager.stop_wsgi()
                            shared_server_manager.stop_cloud()
                        sys.exit(0)
                    
                    curses.endwin()
                    should_logout, shared_server_manager = run_tui_mode(
                        skip_instance_check=not first_run,
                        server_manager=shared_server_manager,
                        from_os_mode=True
                    )
                    
                    if not should_logout:
                        if shared_server_manager:
                            shared_server_manager.stop_wsgi()
                            shared_server_manager.stop_cloud()
                        break
                    
                    first_run = False
                    time.sleep(0.3)
                    
            except Exception as e:
                print(f"Login Error: {e}")
                sys.exit(1)
        else:
            main()
    else:
        main()