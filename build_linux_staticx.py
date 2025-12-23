import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

class ShareifyLinuxBuilder:
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.dist_dir = self.script_dir / 'dist_linux'
        self.build_dir = self.script_dir / 'build_linux'
        self.pyinstaller_dist = self.script_dir / 'dist' / 'shareify_linux'

    def log(self, message, level='INFO'):
        print(f'[{level}] {message}')

    def check_linux(self):
        if sys.platform != 'linux':
            self.log('This script must run on Linux for StaticX builds', 'ERROR')
            return False
        return True

    def ensure_dependencies(self):
        deps = ['pyinstaller', 'staticx', 'patchelf']
        missing = []
        
        try:
            __import__('PyInstaller')
            self.log('✓ PyInstaller available')
        except ImportError:
            missing.append('pyinstaller')
        
        try:
            subprocess.run(['staticx', '--version'], capture_output=True, check=True)
            self.log('✓ StaticX available')
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log('Installing staticx...', 'WARN')
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'staticx'])
                self.log('✓ StaticX installed')
            except subprocess.CalledProcessError:
                missing.append('staticx')
        
        try:
            subprocess.run(['patchelf', '--version'], capture_output=True, check=True)
            self.log('✓ patchelf available')
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log('patchelf not found. Install via: sudo apt install patchelf', 'WARN')
            missing.append('patchelf')
        
        if missing:
            self.log(f'Missing dependencies: {", ".join(missing)}', 'ERROR')
            if 'pyinstaller' in missing:
                self.log('Run: pip install pyinstaller', 'ERROR')
            if 'patchelf' in missing:
                self.log('Run: sudo apt install patchelf', 'ERROR')
            return False
        
        return True

    def create_wrapper_script(self):
        wrapper_content = '''#!/usr/bin/env python3
import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):
    bundle_dir = Path(sys._MEIPASS)
    exe_dir = Path(sys.executable).parent
else:
    bundle_dir = Path(__file__).parent
    exe_dir = bundle_dir

settings_dir = exe_dir / 'settings'
db_dir = exe_dir / 'db'
web_dir = exe_dir / 'web'

if not settings_dir.exists():
    settings_dir.mkdir(parents=True, exist_ok=True)
if not db_dir.exists():
    db_dir.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(bundle_dir))

os.chdir(exe_dir)

if __name__ == "__main__":
    try:
        import launcher
        launcher.main()
    except ImportError as e:
        print(f"Error importing launcher: {e}")
        print(f"Bundle dir: {bundle_dir}")
        print(f"Exe dir: {exe_dir}")
        print(f"Python path: {sys.path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running Shareify: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
'''
        wrapper_path = self.script_dir / 'shareify_wrapper.py'
        with open(wrapper_path, 'w') as f:
            f.write(wrapper_content)
        self.log(f'✓ Wrapper script created: {wrapper_path}')
        return wrapper_path

    def create_spec_file(self, wrapper_script):
        spec_content = f'''import os
from pathlib import Path

block_cipher = None

executable_dir = Path(r"{self.script_dir}")

python_files = []
for py_file in executable_dir.glob("*.py"):
    if py_file.name not in ['build_executable.py', 'build_linux_staticx.py', 
                             'shareify_wrapper.py', 'setup.py']:
        python_files.append(str(py_file))

datas = []

web_dir = executable_dir / 'web'
if web_dir.exists():
    datas.append((str(web_dir), 'web'))

a = Analysis(
    [r'{wrapper_script}'] + python_files,
    pathex=[r'{self.script_dir}'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'launcher',
        'main',
        'update',
        'cloud_connection',
        'install',
        'startup',
        'wsgi',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='shareify_linux',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        spec_path = self.script_dir / 'shareify_linux.spec'
        with open(spec_path, 'w') as f:
            f.write(spec_content)
        self.log(f'✓ Spec file created: {spec_path}')
        return spec_path

    def build_with_pyinstaller(self, spec_path):
        self.log('Building with PyInstaller (onefile)...')
        
        old_dist = self.script_dir / 'dist'
        old_build = self.script_dir / 'build'
        
        if old_dist.exists():
            shutil.rmtree(old_dist)
        if old_build.exists():
            shutil.rmtree(old_build)
        
        try:
            cmd = [sys.executable, '-m', 'PyInstaller', '--clean', str(spec_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.script_dir)
            
            if result.returncode != 0:
                self.log('PyInstaller build failed', 'ERROR')
                self.log(f'STDERR: {result.stderr}')
                return False
            
            self.log('✓ PyInstaller build complete')
            return True
        except Exception as e:
            self.log(f'Error during PyInstaller build: {e}', 'ERROR')
            return False

    def apply_staticx(self):
        pyinstaller_exe = self.script_dir / 'dist' / 'shareify_linux'
        
        if not pyinstaller_exe.exists():
            self.log(f'PyInstaller output not found: {pyinstaller_exe}', 'ERROR')
            return False
        
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        staticx_exe = self.dist_dir / 'shareify'
        
        self.log('Applying StaticX for portability...')
        
        try:
            cmd = ['staticx', str(pyinstaller_exe), str(staticx_exe)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log('StaticX failed', 'ERROR')
                self.log(f'STDERR: {result.stderr}')
                return False
            
            staticx_exe.chmod(0o755)
            self.log(f'✓ StaticX binary created: {staticx_exe}')
            return True
        except Exception as e:
            self.log(f'Error applying StaticX: {e}', 'ERROR')
            return False

    def copy_external_resources(self):
        self.log('Copying settings and database folders...')
        
        settings_src = self.script_dir / 'settings'
        settings_dst = self.dist_dir / 'settings'
        
        if settings_src.exists():
            if settings_dst.exists():
                shutil.rmtree(settings_dst)
            shutil.copytree(settings_src, settings_dst)
            self.log(f'✓ Copied settings: {settings_dst}')
        else:
            self.log('settings/ not found, skipping', 'WARN')
        
        db_src = self.script_dir / 'db'
        db_dst = self.dist_dir / 'db'
        
        if db_src.exists():
            if db_dst.exists():
                shutil.rmtree(db_dst)
            shutil.copytree(db_src, db_dst)
            self.log(f'✓ Copied db: {db_dst}')
        else:
            self.log('db/ not found, creating empty directory', 'WARN')
            db_dst.mkdir(parents=True, exist_ok=True)
        
        web_src = self.script_dir / 'web'
        web_dst = self.dist_dir / 'web'
        
        if web_src.exists():
            if web_dst.exists():
                shutil.rmtree(web_dst)
            shutil.copytree(web_src, web_dst)
            self.log(f'✓ Copied web: {web_dst}')
        else:
            self.log('web/ not found, skipping', 'WARN')

    def cleanup(self):
        temp_files = [
            self.script_dir / 'shareify_wrapper.py',
            self.script_dir / 'shareify_linux.spec',
            self.script_dir / 'dist',
            self.script_dir / 'build',
        ]
        
        for path in temp_files:
            try:
                if path.exists():
                    if path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(path)
            except Exception as e:
                self.log(f'Could not remove {path}: {e}', 'WARN')

    def build(self):
        self.log('=' * 60)
        self.log('Shareify Linux StaticX Builder')
        self.log('=' * 60)
        
        if not self.check_linux():
            return False
        
        if not self.ensure_dependencies():
            return False
        
        wrapper = self.create_wrapper_script()
        spec = self.create_spec_file(wrapper)
        
        if not self.build_with_pyinstaller(spec):
            return False
        
        if not self.apply_staticx():
            return False
        
        self.copy_external_resources()
        self.cleanup()
        
        self.log('=' * 60)
        self.log('✓ Build Complete!')
        self.log('=' * 60)
        self.log(f'Output directory: {self.dist_dir}')
        self.log(f'Executable: {self.dist_dir / "shareify"}')
        self.log('')
        self.log('The build includes:')
        self.log('  - Portable static binary (shareify)')
        self.log('  - settings/ folder (editable JSON configs)')
        self.log('  - db/ folder (SQLite databases)')
        self.log('  - web/ folder (web interface)')
        self.log('')
        self.log('To deploy: Copy the entire dist_linux/ folder to target system')
        
        return True

def main():
    builder = ShareifyLinuxBuilder()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--clean':
        if builder.dist_dir.exists():
            shutil.rmtree(builder.dist_dir)
            print('✓ Cleaned dist_linux/')
        if builder.build_dir.exists():
            shutil.rmtree(builder.build_dir)
            print('✓ Cleaned build_linux/')
        
        temp_files = [
            builder.script_dir / 'shareify_wrapper.py',
            builder.script_dir / 'shareify_linux.spec',
            builder.script_dir / 'dist',
            builder.script_dir / 'build',
        ]
        for f in temp_files:
            if f.exists():
                if f.is_file():
                    f.unlink()
                else:
                    shutil.rmtree(f)
        print('✓ Cleaned temp files')
        return
    
    success = builder.build()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
