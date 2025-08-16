from wsgiref.simple_server import make_server
from cloud_command import application as cloud_app

def main():
    try:
        wsgi_server = make_server('0.0.0.0', 25841, cloud_app)
        print("Cloud Command server is running and ready to accept connections")
        wsgi_server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Cloud Command server...")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: Port 25841 is already in use. Please stop any existing server or choose a different port.")
        else:
            print(f"Error starting Cloud Command server: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
