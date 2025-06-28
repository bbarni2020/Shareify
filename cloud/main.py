import eventlet
eventlet.monkey_patch()

from server import create_app, socketio

application = create_app()

if __name__ == '__main__':
    socketio.run(application, host='0.0.0.0', port=5698, use_reloader=False, log_output=True)
