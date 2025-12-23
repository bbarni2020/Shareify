import eventlet
eventlet.monkey_patch()

import threading
from server import create_app, socketio
from cloud_command import application as cloud_app
from wsgiref.simple_server import make_server

socketio_app = create_app()

def start_socketio_server():
    socketio.run(socketio_app, host='0.0.0.0', port=5698, use_reloader=False, log_output=True)

def start_wsgi_server():
    wsgi_server = make_server('0.0.0.0', 25841, cloud_app)
    wsgi_server.serve_forever()

if __name__ == '__main__':
    
    socketio_thread = threading.Thread(target=start_socketio_server, daemon=True)
    wsgi_thread = threading.Thread(target=start_wsgi_server, daemon=True)
    
    socketio_thread.start()
    wsgi_thread.start()
    
    try:
        socketio_thread.join()
        wsgi_thread.join()
    except KeyboardInterrupt:
        print("\nShutting down servers...")