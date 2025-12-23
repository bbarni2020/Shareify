import eventlet
eventlet.monkey_patch()

from server import create_app, socketio

def main():    
    socketio_app = create_app()
    
    try:
        socketio.run(
            socketio_app, 
            host='0.0.0.0', 
            port=5698, 
            use_reloader=False, 
            log_output=True,
            debug=False
        )
    except KeyboardInterrupt:
        print("\nShutting down SocketIO server...")
    except Exception as e:
        print(f"Error starting SocketIO server: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
