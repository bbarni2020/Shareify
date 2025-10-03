__version__ = '1.0.0'
__author__ = 'Shareify Team'
__description__ = 'Simple file sharing server with web interface'
try:
    from .main import create_app, app
    from .launcher import main as launcher_main
    from .install import main as install_main
    from .update import update as update_main
except ImportError:
    pass