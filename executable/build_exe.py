import os
import sys
import subprocess
import shutil
import json
import tempfile
from pathlib import Path

class ShareifyBuilder:

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.dist_dir = self.script_dir / 'dist'
        self.build_dir = self.script_dir / 'build'

    def log(self, message, level='INFO'):
        print(f'[{level}] {message}')

    def ensure_dependencies(self):
        self.log('Checking and installing dependencies...')
        dependencies = ['pyinstaller', 'flask', 'flask-cors', 'flask-limiter', 'werkzeug', 'jinja2', 'colorama', 'psutil', 'pyftpdlib', 'requests', 'PyJWT', 'gunicorn', 'python-socketio', 'websocket-client']
        for dep in dependencies:
            try:
                __import__(dep.replace('-', '_'))
                self.log(f'✓ {dep} is available')
            except ImportError:
                self.log(f'Installing {dep}...')
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
                    self.log(f'✓ {dep} installed successfully')
                except subprocess.CalledProcessError:
                    self.log(f'✗ Failed to install {dep}', 'ERROR')
                    return False
        return True

    def create_main_executable_script(self):
        main_script = '#!/usr/bin/env python3\n"""\nShareify Main Executable Entry Point\n"""\nimport sys\nimport os\n\n# Add the application directory to Python path\nif getattr(sys, \'frozen\', False):\n    # Running in PyInstaller bundle\n    application_path = sys._MEIPASS\nelse:\n    # Running in normal Python environment\n    application_path = os.path.dirname(os.path.abspath(__file__))\n\nsys.path.insert(0, application_path)\n\n# Import and run the main application\nif __name__ == "__main__":\n    try:\n        from main import main\n        main()\n    except ImportError as e:\n        print(f"Error importing main module: {e}")\n        print("Make sure all dependencies are installed.")\n        sys.exit(1)\n    except Exception as e:\n        print(f"Error running Shareify: {e}")\n        sys.exit(1)\n'
        entry_script_path = self.script_dir / 'shareify_main.py'
        with open(entry_script_path, 'w') as f:
            f.write(main_script)
        self.log(f'✓ Created main executable script: {entry_script_path}')
        return entry_script_path

    def create_pyinstaller_spec(self, entry_script):
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-\nimport os\n\nblock_cipher = None\n\n# Collect all data files\ndatas = []\n\n# Add web directory\nweb_dir = r"{self.script_dir / 'web'}"\nif os.path.exists(web_dir):\n    datas.append((web_dir, 'web'))\n\n# Add settings directory  \nsettings_dir = r"{self.script_dir / 'settings'}"\nif os.path.exists(settings_dir):\n    datas.append((settings_dir, 'settings'))\n\n# Add db directory\ndb_dir = r"{self.script_dir / 'db'}"\nif os.path.exists(db_dir):\n    datas.append((db_dir, 'db'))\n\n# Add requirements file\nreq_file = r"{self.script_dir / 'requirements.txt'}"\nif os.path.exists(req_file):\n    datas.append((req_file, '.'))\n\na = Analysis(\n    [r'{entry_script}'],\n    pathex=[r'{self.script_dir}'],\n    binaries=[],\n    datas=datas,\n    hiddenimports=[\n        'flask',\n        'flask_cors', \n        'flask_limiter',\n        'flask_limiter.util',\n        'werkzeug',\n        'werkzeug.utils',\n        'jinja2',\n        'colorama',\n        'psutil',\n        'pyftpdlib',\n        'pyftpdlib.authorizers',\n        'pyftpdlib.handlers', \n        'pyftpdlib.servers',\n        'requests',\n        'jwt',\n        'sqlite3',\n        'threading',\n        'json',\n        'os',\n        'sys',\n        'datetime',\n        'mimetypes',\n        'secrets',\n        'tempfile',\n        'zipfile',\n        'shutil',\n        'ctypes',\n        'gunicorn',\n        'socketio',\n        'websocket',\n        'main',\n        'update',\n        'launcher',\n        'install',\n        'wsgi',\n        'startup',\n        'venv_manager',\n        'cloud_connection',\n    ],\n    hookspath=[],\n    hooksconfig={{}},\n    runtime_hooks=[],\n    excludes=[],\n    win_no_prefer_redirects=False,\n    win_private_assemblies=False,\n    cipher=block_cipher,\n    noarchive=False,\n)\n\npyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)\n\nexe = EXE(\n    pyz,\n    a.scripts,\n    a.binaries,\n    a.zipfiles,\n    a.datas,\n    [],\n    name='shareify',\n    debug=False,\n    bootloader_ignore_signals=False,\n    strip=False,\n    upx=True,\n    upx_exclude=[],\n    runtime_tmpdir=None,\n    console=True,\n    disable_windowed_traceback=False,\n    argv_emulation=False,\n    target_arch=None,\n    codesign_identity=None,\n    entitlements_file=None,\n)\n"""
        spec_path = self.script_dir / 'shareify.spec'
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        self.log(f'✓ Created PyInstaller spec: {spec_path}')
        return spec_path

    def build_executable(self, spec_path):
        self.log('Building executable with PyInstaller...')
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        try:
            cmd = [sys.executable, '-m', 'PyInstaller', '--clean', str(spec_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.script_dir)
            if result.returncode == 0:
                self.log('✓ Executable built successfully!')
                if os.name == 'nt':
                    exe_path = self.dist_dir / 'shareify.exe'
                else:
                    exe_path = self.dist_dir / 'shareify'
                if exe_path.exists():
                    self.log(f'✓ Executable created: {exe_path}')
                    return exe_path
                else:
                    self.log('✗ Executable not found after build', 'ERROR')
                    return None
            else:
                self.log('✗ PyInstaller build failed', 'ERROR')
                self.log(f'STDOUT: {result.stdout}')
                self.log(f'STDERR: {result.stderr}')
                return None
        except Exception as e:
            self.log(f'✗ Error during build: {e}', 'ERROR')
            return None

    def create_distribution_package(self, exe_path):
        self.log('Creating distribution package...')
        package_dir = self.script_dir / 'shareify_package'
        if package_dir.exists():
            shutil.rmtree(package_dir)
        package_dir.mkdir()
        shutil.copy2(exe_path, package_dir / exe_path.name)
        essential_files = ['requirements.txt', 'README.md', 'LICENSE']
        for file_name in essential_files:
            file_path = self.script_dir / file_name
            if file_path.exists():
                shutil.copy2(file_path, package_dir / file_name)
        essential_dirs = ['web', 'settings', 'db']
        for dir_name in essential_dirs:
            dir_path = self.script_dir / dir_name
            if dir_path.exists():
                shutil.copytree(dir_path, package_dir / dir_name)
        self.log(f'✓ Distribution package created: {package_dir}')
        return package_dir

    def create_installer_script(self, package_dir):
        installer_content = '@echo off\necho Installing Shareify...\n\nREM Create installation directory\nset INSTALL_DIR=%PROGRAMFILES%\\Shareify\nif not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"\n\nREM Copy files\nxcopy /E /I /Y . "%INSTALL_DIR%"\n\nREM Create desktop shortcut\nset DESKTOP=%USERPROFILE%\\Desktop\necho [InternetShortcut] > "%DESKTOP%\\Shareify.url"\necho URL=file:///%INSTALL_DIR%\\shareify.exe >> "%DESKTOP%\\Shareify.url"\n\necho Shareify installed successfully!\necho You can run it from: %INSTALL_DIR%\\shareify.exe\npause\n'
        installer_path = package_dir / 'install.bat'
        with open(installer_path, 'w') as f:
            f.write(installer_content)
        self.log(f'✓ Created installer script: {installer_path}')
        return installer_path

    def cleanup_temp_files(self):
        self.log('Cleaning up temporary files...')
        temp_files = ['shareify_main.py', 'shareify.spec']
        for file_name in temp_files:
            file_path = self.script_dir / file_name
            if file_path.exists():
                file_path.unlink()
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.log('✓ Cleanup completed')

    def build(self):
        self.log('Starting Shareify executable build process...')
        self.log('=' * 60)
        if not self.ensure_dependencies():
            self.log('✗ Dependency installation failed', 'ERROR')
            return False
        entry_script = self.create_main_executable_script()
        spec_path = self.create_pyinstaller_spec(entry_script)
        exe_path = self.build_executable(spec_path)
        if not exe_path:
            return False
        package_dir = self.create_distribution_package(exe_path)
        self.create_installer_script(package_dir)
        self.cleanup_temp_files()
        self.log('=' * 60)
        self.log('✓ Shareify executable build completed successfully!')
        self.log(f'✓ Executable: {exe_path}')
        self.log(f'✓ Package: {package_dir}')
        self.log('=' * 60)
        return True

def main():
    builder = ShareifyBuilder()
    if len(sys.argv) > 1:
        if sys.argv[1] == '--clean':
            builder.cleanup_temp_files()
            if builder.dist_dir.exists():
                shutil.rmtree(builder.dist_dir)
            package_dir = builder.script_dir / 'shareify_package'
            if package_dir.exists():
                shutil.rmtree(package_dir)
            print('Cleaned all build files')
            return
    success = builder.build()
    if not success:
        sys.exit(1)
if __name__ == '__main__':
    main()