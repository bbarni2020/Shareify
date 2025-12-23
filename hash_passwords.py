import os
import sqlite3
import shutil
import argparse
import glob

try:
    import bcrypt
except Exception:
    bcrypt = None


def backup_file(path):
    backup = path + '.bak'
    shutil.copy2(path, backup)
    return backup


def hash_value(val):
    if not val:
        return val
    if isinstance(val, bytes):
        val = val.decode('utf-8')
    if val.startswith('$2b$') or val.startswith('$2y$'):
        return val
    if bcrypt:
        try:
            return bcrypt.hashpw(val.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except Exception:
            return val
    return val


def migrate_db(db_path, dry_run=False):
    print(f"Processing: {db_path}")
    if not os.path.exists(db_path):
        print("  -> Skipped (not found)")
        return

    backup = backup_file(db_path)
    print(f"  -> Backup created: {backup}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT id, password FROM users')
        rows = cursor.fetchall()
        for uid, pwd in rows:
            if pwd is None:
                continue
            new = hash_value(pwd)
            if new != pwd:
                print(f"  -> Updating users.id={uid}")
                if not dry_run:
                    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (new, uid))
    except Exception as e:
        print(f"  -> users table: {e}")

    try:
        cursor.execute('SELECT id, password FROM ftp_users')
        rows = cursor.fetchall()
        for uid, pwd in rows:
            if pwd is None:
                continue
            new = hash_value(pwd)
            if new != pwd:
                print(f"  -> Updating ftp_users.id={uid}")
                if not dry_run:
                    cursor.execute('UPDATE ftp_users SET password = ? WHERE id = ?', (new, uid))
    except Exception as e:
        print(f"  -> ftp_users table: {e}")

    if not dry_run:
        conn.commit()
    conn.close()


def find_and_migrate(root_dirs, dry_run=False):
    candidates = []
    for root in root_dirs:
        pattern = os.path.join(root, '**', 'db', 'users.db')
        found = glob.glob(pattern, recursive=True)
        for f in found:
            candidates.append(f)

    extras = [os.path.join(os.path.dirname(__file__), '..', 'host', 'db', 'users.db'),
              os.path.join(os.path.dirname(__file__), '..', 'current', 'db', 'users.db'),
              os.path.join(os.path.dirname(__file__), '..', 'executable', 'db', 'users.db')]
    for e in extras:
        e = os.path.normpath(e)
        if os.path.exists(e) and e not in candidates:
            candidates.append(e)

    candidates = sorted(set(candidates))
    if not candidates:
        print("No users.db files found to migrate.")
        return

    for db in candidates:
        migrate_db(db, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(description='Hash plaintext passwords in Shareify sqlite DBs')
    parser.add_argument('--root', '-r', action='append', help='Root folders to search (defaults to repository root)', default=[os.path.join(os.path.dirname(__file__), '..')])
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without writing')
    args = parser.parse_args()
    roots = [os.path.abspath(r) for r in args.root]
    find_and_migrate(roots, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
