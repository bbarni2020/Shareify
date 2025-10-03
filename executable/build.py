import os
import sys
import subprocess
import shutil
from pathlib import Path

def ensure_pyinstaller():
    try:
        import PyInstaller
        print('✓ PyInstaller is already installed')
        return True
    except ImportError:
        print('Installing PyInstaller...')
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
            print('✓ PyInstaller installed successfully')
            return True
        except subprocess.CalledProcessError:
            print('✗ Failed to install PyInstaller')
            return False

def create_spec_file():
    spec_content = "# -*- mode: python ; coding: utf-8 -*-\n\nblock_cipher = None\n\na = Analysis(\n    ['main.py'],\n    pathex=[],\n    binaries=[],\n    datas=[\n        ('web', 'web'),\n        ('web/assets', 'web/assets'),\n        ('settings', 'settings'),\n        ('db', 'db'),\n        ('requirements.txt', '.'),\n    ],\n    hiddenimports=[\n        'flask',\n        'flask_cors',\n        'flask_limiter',\n        'werkzeug',\n        'jinja2',\n        'colorama',\n        'psutil',\n        'pyftpdlib',\n        'requests',\n        'jwt',\n        'sqlite3',\n        'threading',\n        'json',\n        'os',\n        'sys',\n        'datetime',\n        'mimetypes',\n        'secrets',\n        'tempfile',\n        'zipfile',\n        'shutil',\n        'ctypes',\n    ],\n    hookspath=[],\n    hooksconfig={},\n    runtime_hooks=[],\n    excludes=[],\n    win_no_prefer_redirects=False,\n    win_private_assemblies=False,\n    cipher=block_cipher,\n    noarchive=False,\n)\n\npyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)\n\nexe = EXE(\n    pyz,\n    a.scripts,\n    a.binaries,\n    a.zipfiles,\n    a.datas,\n    [],\n    name='shareify',\n    debug=False,\n    bootloader_ignore_signals=False,\n    strip=False,\n    upx=True,\n    upx_exclude=[],\n    runtime_tmpdir=None,\n    console=True,\n    disable_windowed_traceback=False,\n    argv_emulation=False,\n    target_arch=None,\n    codesign_identity=None,\n    entitlements_file=None,\n    icon=None,\n)\n"
    with open('shareify.spec', 'w') as f:
        f.write(spec_content)
    print('✓ Created shareify.spec file')

def build_executable():
    print('Building Shareify executable...')
    try:
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        if os.path.exists('build'):
            shutil.rmtree('build')
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'shareify.spec']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print('✓ Executable built successfully!')
            if os.name == 'nt':
                exe_path = Path('dist/shareify.exe')
            else:
                exe_path = Path('dist/shareify')
            if exe_path.exists():
                print(f'✓ Executable location: {exe_path.absolute()}')
                return True
            else:
                print('✗ Executable not found in expected location')
                return False
        else:
            print('✗ Build failed!')
            print('STDOUT:', result.stdout)
            print('STDERR:', result.stderr)
            return False
    except Exception as e:
        print(f'✗ Error during build: {e}')
        return False

def main():
    print('=' * 50)
    print('Shareify Executable Builder')
    print('=' * 50)
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f'Working directory: {script_dir}')
    if not ensure_pyinstaller():
        sys.exit(1)
    create_spec_file()
    if build_executable():
        print('\n' + '=' * 50)
        print('Build completed successfully!')
        print("Your executable is ready in the 'dist' folder.")
        print('=' * 50)
    else:
        print('\n' + '=' * 50)
        print('Build failed!')
        print('Please check the error messages above.')
        print('=' * 50)
        sys.exit(1)
if __name__ == '__main__':
    main()