import sys
import os
import json
import update

sys.path.insert(0, os.path.dirname(__file__))

def load_settings():
    settings_file = os.path.join(os.path.dirname(__file__), "settings/settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("Error: Invalid JSON format in settings file.")
                return None
    else:
        print(f"Settings file '{settings_file}' not found.")
        return None

settings = load_settings()

from main import create_app

application = create_app()

if __name__ == "__main__":
    try:
        from gunicorn.app.base import BaseApplication
    except Exception:
        raise SystemExit("gunicorn is required: pip install gunicorn")

    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.application = app
            self.options = options or {}
            super().__init__()
        def load_config(self):
            cfg = {k: v for k, v in self.options.items() if k in self.cfg.settings and v is not None}
            for k, v in cfg.items():
                self.cfg.set(k.lower(), v)
        def load(self):
            return self.application

    host = (settings or {}).get('host', '127.0.0.1')
    port = int((settings or {}).get('port', 6969))
    options = {
        'bind': f'{host}:{port}',
        'workers': int(os.environ.get('GUNICORN_WORKERS', '4')),
        'worker_class': os.environ.get('GUNICORN_WORKER_CLASS', 'gthread'),
        'threads': int(os.environ.get('GUNICORN_THREADS', '4')),
        'timeout': int(os.environ.get('GUNICORN_TIMEOUT', '60')),
        'accesslog': '-',
        'errorlog': '-',
        'loglevel': os.environ.get('GUNICORN_LOGLEVEL', 'info')
    }
    StandaloneApplication(application, options).run()
