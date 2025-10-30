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

def run_tui_mode():
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
        
        server_manager = ServerManager()
        selected_option = 0
        
        if sys.platform.startswith('linux'):
            menu_items = [
                "Toggle Shareify Server",
                "Toggle Cloud Connection",
                "WiFi Networks"
            ]
        else:
            menu_items = [
                "Toggle Shareify Server",
                "Toggle Cloud Connection"
            ]
        
        last_status_check = 0
        status_cache = {'wsgi': False, 'cloud': False}
        
        if _already_running():
            stdscr.addstr(0, 0, "Another instance is already running", curses.color_pair(2))
            stdscr.refresh()
            time.sleep(2)
            return
        
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
                
                if height < 30 or width < 100:
                    stdscr.addstr(0, 0, "Terminal too small! Resize to at least 100x30", curses.color_pair(2))
                    stdscr.refresh()
                    key = stdscr.getch()
                    if key == ord('q') or key == ord('Q'):
                        break
                    continue
                
                draw_ascii_art(stdscr, 2, (width - 36) // 2)
                
                title_line = "━" * (width - 4)
                stdscr.addstr(1, 2, title_line, curses.color_pair(5))
                stdscr.addstr(8, 2, title_line, curses.color_pair(5))
                
                stats_y = 10
                stats_x = 4
                stats_width = width // 2 - 6
                stats_height = 14
                
                draw_box(stdscr, stats_y, stats_x, stats_height, stats_width, "System Status", 4)
                
                cloud_status = "Running" if status_cache['cloud'] else "Stopped"
                cloud_active = status_cache['cloud']
                
                ftp_status = get_ftp_status()
                ftp_active = ftp_status == "Running"
                
                shareify_status = "Running" if status_cache['wsgi'] else "Stopped"
                shareify_active = status_cache['wsgi']
                
                network_status = get_network_status()
                network_active = network_status == "Online"
                
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                draw_status_indicator(stdscr, stats_y + 2, stats_x + 3, "Shareify Server", shareify_status, shareify_active)
                draw_status_indicator(stdscr, stats_y + 4, stats_x + 3, "Cloud Connection", cloud_status, cloud_active)
                draw_status_indicator(stdscr, stats_y + 6, stats_x + 3, "FTP Server", ftp_status, ftp_active)
                draw_status_indicator(stdscr, stats_y + 8, stats_x + 3, "Network Status", network_status, network_active)
                
                stdscr.addstr(stats_y + 11, stats_x + 3, "⏰ ", curses.color_pair(3))
                stdscr.addstr(stats_y + 11, stats_x + 5, "Time", curses.color_pair(4))
                stdscr.addstr(stats_y + 11, stats_x + 25, current_time, curses.color_pair(6) | curses.A_BOLD)
                
                options_y = stats_y
                options_x = width // 2 + 2
                options_width = width // 2 - 6
                options_height = stats_height
                
                if not wifi_mode:
                    draw_box(stdscr, options_y, options_x, options_height, options_width, "Controls", 4)
                    
                    for idx, item in enumerate(menu_items):
                        item_y = options_y + 2 + idx * 3
                        draw_button(stdscr, item_y, options_x + 4, item, idx == selected_option, 4)
                else:
                    if sys.platform.startswith('linux'):
                        draw_box(stdscr, options_y, options_x, options_height + 12, options_width, "WiFi Networks", 4)
                        
                        current_wifi = get_current_wifi()
                        wifi_strength = get_wifi_signal_strength()
                        
                        if current_wifi:
                            stdscr.addstr(options_y + 2, options_x + 4, "● ", curses.color_pair(1) | curses.A_BOLD)
                            stdscr.addstr(options_y + 2, options_x + 6, "Connected:", curses.color_pair(4))
                            stdscr.addstr(options_y + 2, options_x + 18, current_wifi, curses.color_pair(1) | curses.A_BOLD)
                            
                            stdscr.addstr(options_y + 3, options_x + 6, "Signal:", curses.color_pair(4))
                            stdscr.addstr(options_y + 3, options_x + 18, wifi_strength, curses.color_pair(3))
                            
                            stdscr.addstr(options_y + 4, options_x + 4, "─" * (options_width - 8), curses.color_pair(7))
                            
                            net_start_y = options_y + 5
                        else:
                            stdscr.addstr(options_y + 2, options_x + 4, "○ ", curses.color_pair(2))
                            stdscr.addstr(options_y + 2, options_x + 6, "Not connected to WiFi", curses.color_pair(2))
                            stdscr.addstr(options_y + 3, options_x + 4, "─" * (options_width - 8), curses.color_pair(7))
                            net_start_y = options_y + 4
                    else:
                        wifi_mode = False
                        continue
                    
                    if not wifi_networks:
                        stdscr.addstr(net_start_y, options_x + 4, "⟳ Scanning for networks...", curses.color_pair(3) | curses.A_BOLD)
                    else:
                        stdscr.addstr(net_start_y, options_x + 4, "Available Networks:", curses.color_pair(6))
                        for idx, net in enumerate(wifi_networks[:5]):
                            item_y = net_start_y + 1 + idx * 2
                            is_current = (net == current_wifi)
                            if idx == wifi_selected:
                                stdscr.addstr(item_y, options_x + 4, "▶ ", curses.color_pair(3) | curses.A_BOLD)
                                if is_current:
                                    stdscr.addstr(item_y, options_x + 6, net + " ✓", curses.color_pair(1) | curses.A_REVERSE | curses.A_BOLD)
                                else:
                                    stdscr.addstr(item_y, options_x + 6, net, curses.color_pair(4) | curses.A_REVERSE | curses.A_BOLD)
                            else:
                                if is_current:
                                    stdscr.addstr(item_y, options_x + 4, "  " + net + " ✓", curses.color_pair(1))
                                else:
                                    stdscr.addstr(item_y, options_x + 4, "  " + net, curses.color_pair(6))
                        
                        help_y = options_y + options_height + 10
                        stdscr.addstr(help_y, options_x + 4, "↵ Connect", curses.color_pair(1))
                        stdscr.addstr(help_y, options_x + 20, "ESC Back", curses.color_pair(2))
                
                footer_y = height - 2
                footer_text = "↑↓ Navigate  •  ↵ Select  •  Mouse Enabled"
                stdscr.addstr(footer_y, (width - len(footer_text)) // 2, footer_text, curses.color_pair(7))
                
                exit_hint = "Ctrl+C to exit"
                stdscr.addstr(footer_y, width - len(exit_hint) - 2, exit_hint, curses.color_pair(7))
                
                if message and time.time() - message_time < 3:
                    msg_y = height - 4
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
                                    item_y = options_y + 2 + idx * 3
                                    if my == item_y and mx >= options_x + 4 and mx < options_x + options_width - 4:
                                        selected_option = idx
                                        key = ord('\n')
                                        break
                            else:
                                current_wifi = get_current_wifi()
                                net_start_y = options_y + 5 if current_wifi else options_y + 4
                                for idx in range(min(5, len(wifi_networks))):
                                    item_y = net_start_y + 1 + idx * 2
                                    if my == item_y and mx >= options_x + 4 and mx < options_x + options_width - 4:
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
        
        server_manager.stop_wsgi()
        server_manager.stop_cloud()
    
    try:
        curses.wrapper(tui_main)
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
    
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'tui':
        run_tui_mode()
    else:
        main()