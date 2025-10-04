import os
import sys
import subprocess
import shutil
import json
import tempfile
from pathlib import Path

class ShareifyExecutableBuilder:

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.dist_dir = self.script_dir / 'dist'
        self.build_dir = self.script_dir / 'build'

    def log(self, message, level='INFO'):
        print(f'[{level}] {message}')

    def ensure_pyinstaller(self):
        try:
            __import__('PyInstaller')
            self.log('✓ PyInstaller is available')
            return True
        except ImportError:
            self.log('Installing PyInstaller...')
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
                self.log('✓ PyInstaller installed')
                return True
            except subprocess.CalledProcessError:
                self.log('✗ Failed to install PyInstaller', 'ERROR')
                return False

    def create_main_script(self):
        main_script = '''import sys
import os

if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

if __name__ == "__main__":
    try:
        import launcher
        launcher.main()
    except ImportError as e:
        print(f"Error importing launcher module: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running Shareify: {e}")
        sys.exit(1)
'''
        entry_script_path = self.script_dir / 'shareify_entry.py'
        with open(entry_script_path, 'w') as f:
            f.write(main_script)
        self.log(f'✓ Created entry script: {entry_script_path}')
        return entry_script_path

    def create_spec_file(self, entry_script):
        icon_path = self.script_dir / 'web' / 'assets' / 'icon.ico'

        spec_content = f'''import os
from pathlib import Path

block_cipher = None

datas = []

executable_dir = r"{self.script_dir}"
python_files = []
for py_file in Path(executable_dir).glob("*.py"):
    if py_file.name not in ['build_executable.py', 'shareify_entry.py']:
        python_files.append(str(py_file))

web_dir = r"{self.script_dir / 'web'}"
if os.path.exists(web_dir):
    datas.append((web_dir, 'web'))

settings_dir = r"{self.script_dir / 'settings'}"
if os.path.exists(settings_dir):
    datas.append((settings_dir, 'settings'))

db_dir = r"{self.script_dir / 'db'}"
if os.path.exists(db_dir):
    datas.append((db_dir, 'db'))

icon_candidate = r"{icon_path}"
if not os.path.exists(icon_candidate):
    icon_candidate = None

a = Analysis(
    [r'{entry_script}'] + python_files,
    pathex=[r'{self.script_dir}'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'main',
        'launcher', 
        'install',
        'update',
        'cloud_connection',
        'venv_manager',
        'startup',
        'flask',
        'flask_cors',
        'flask_limiter',
        'werkzeug',
        'jinja2',
        'colorama',
        'psutil',
        'pyftpdlib',
        'requests',
        'jwt',
        'sqlite3',
        'gunicorn',
        'socketio',
        'websocket',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='shareify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_candidate,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='shareify',
)
'''
        spec_path = self.script_dir / 'shareify.spec'
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        self.log(f'✓ Created spec file: {spec_path}')
        return spec_path

    def build_executable(self, spec_path):
        self.log('Building executable...')
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        
        try:
            cmd = [sys.executable, '-m', 'PyInstaller', '--clean', str(spec_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.script_dir)
            
            if result.returncode == 0:
                self.log('✓ Executable built successfully!')
                return True
            else:
                self.log('✗ PyInstaller build failed', 'ERROR')
                self.log(f'STDERR: {result.stderr}')
                return False
        except Exception as e:
            self.log(f'✗ Error during build: {e}', 'ERROR')
            return False
        
        return True

    def cleanup_temp_files(self):
        temp_files = ['shareify_entry.py', 'shareify.spec']
        for file_name in temp_files:
            file_path = self.script_dir / file_name
            if file_path.exists():
                file_path.unlink()
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

    def build(self):
        self.log('Starting Shareify executable build...')
        self.log('=' * 50)
        
        if not self.ensure_pyinstaller():
            return False
        
        entry_script = self.create_main_script()
        spec_path = self.create_spec_file(entry_script)
        
        if not self.build_executable(spec_path):
            return False
        
        
        self.cleanup_temp_files()
        
        self.log('=' * 50)
        self.log('✓ Executable build completed!')
        
        shareify_dist = self.dist_dir / 'shareify'
        if os.name == 'nt':
            exe_path = shareify_dist / 'shareify.exe'
        else:
            exe_path = shareify_dist / 'shareify'
        
        if exe_path.exists():
            self.log(f'✓ Executable: {exe_path}')
        
        self.log(f'✓ Distribution folder: {shareify_dist}')
        self.log('✓ Ready to zip and deploy!')
        
        return True

def main():
    builder = ShareifyExecutableBuilder()
    if len(sys.argv) > 1:
        if sys.argv[1] == '--clean':
            if builder.dist_dir.exists():
                shutil.rmtree(builder.dist_dir)
                print('Cleaned dist directory')
            if builder.build_dir.exists():
                shutil.rmtree(builder.build_dir)
                print('Cleaned build directory')
            return
    
    success = builder.build()
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    main()