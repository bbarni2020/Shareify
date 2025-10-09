from wsgiref.simple_server import make_server, WSGIServer, WSGIRequestHandler
from socketserver import ThreadingMixIn
from cloud_command import application as cloud_app


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    try:
        port = 25841
        wsgi_server = make_server(
            '0.0.0.0',
            port,
            cloud_app,
            server_class=ThreadingWSGIServer,
            handler_class=WSGIRequestHandler,
        )
        print(f"Cloud Command server is running (threaded) on 0.0.0.0:{port}")
        wsgi_server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Cloud Command server...")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: Port {port} is already in use. Please stop any existing server or choose a different port.")
        else:
            print(f"Error starting Cloud Command server: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
