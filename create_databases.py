import sqlite3
import secrets
import os
from pathlib import Path

def create_databases():

    script_dir = Path(__file__).parent.absolute()
    db_dir = script_dir / 'db'
    db_dir.mkdir(parents=True, exist_ok=True)
    users_db_path = db_dir / 'users.db'
    logs_db_path = db_dir / 'logs.db'
    
    print("[Shareify] Creating Shareify databases...")
    try:
        print(f"[Shareify] Creating users database: {users_db_path}")
        conn = sqlite3.connect(users_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            ip TEXT,
            role TEXT NOT NULL,
            ftp_users TEXT,
            paths TEXT,
            settings TEXT,
            API_KEY TEXT NOT NULL,
            paths_write TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ftp_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            homedir TEXT NOT NULL,
            permissions TEXT NOT NULL
        )
        ''')
        
        api_key = secrets.token_hex(32)
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            default_user = {
                'username': 'admin',
                'password': 'root',
                'name': 'Administrator',
                'ip': '',
                'role': 'admin',
                'ftp_users': '',
                'paths': '[""]',
                'settings': '',
                'API_KEY': api_key,
                'paths_write': '[""]'
            }
            
            cursor.execute('''
                INSERT INTO users (username, password, name, ip, role, ftp_users, paths, settings, API_KEY, paths_write)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                default_user['username'],
                default_user['password'],
                default_user['name'],
                default_user['ip'],
                default_user['role'],
                default_user['ftp_users'],
                default_user['paths'],
                default_user['settings'],
                default_user['API_KEY'],
                default_user['paths_write']
            ))
            
            print(f"[Shareify] ✓ Loaded default admin user")
            print(f"[Shareify]   Username: {default_user['username']}")
            print(f"[Shareify]   Password: {default_user['password']}")
            print(f"[Shareify]   API Key: {api_key}")
        else:
            print("[Shareify] ✓ Admin user already exists")
        
        conn.commit()
        conn.close()
        print(f"[Shareify] ✓ Users database loaded successfully")
        
    except Exception as e:
        print(f"[Shareify] ✗ Error creating users database: {e}")
        return False
    
    try:
        print(f"[Shareify] Creating logs database: {logs_db_path}")
        conn = sqlite3.connect(logs_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            ip TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"[Shareify] ✓ Logs database loaded successfully")
        
    except Exception as e:
        print(f"[Shareify] ✗ Error creating logs database: {e}")
        return False

    print("[Shareify] ✓ All databases loaded successfully!")
    print(f"[Shareify] Database location: {db_dir}")
    print(f"[Shareify] Files loaded:")
    print(f"[Shareify]   - {users_db_path}")
    print(f"[Shareify]   - {logs_db_path}")
    
    return True

if __name__ == '__main__':
    create_databases()