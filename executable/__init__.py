__version__ = '1.2.0'
__author__ = 'Balogh Barnabás'
__description__ = 'Shareify is a self-hosted file server that lets you access and share your files from anywhere without subscription fees or upload limits. It runs on your own hardware (old laptop, Raspberry Pi, whatever) and includes a bridge service for remote access without dealing with port forwarding. Think of it as your personal Dropbox that you actually control, with a clean web interface and mobile app for easy file management.'

try:
    import main
    import launcher
    import install
    import update
    import cloud_connection
    import wsgi
except ImportError:
    pass

if __name__ == '__main__':
    import launcher
    launcher.main()