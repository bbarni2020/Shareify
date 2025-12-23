import subprocess
import sys
import os
import platform
from pathlib import Path

def get_script_dir():
    return Path(__file__).parent.absolute()

def get_venv_path():
    return get_script_dir() / "shareify_venv"

def get_venv_python():
    venv_path = get_venv_path()
    if platform.system().lower() == "windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def get_venv_pip():
    venv_path = get_venv_path()
    if platform.system().lower() == "windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"

def venv_exists():
    venv_path = get_venv_path()
    python_exe = get_venv_python()
    return venv_path.exists() and python_exe.exists()

def create_venv():
    venv_path = get_venv_path()
    
    if venv_exists():
        print(f"Virtual environment already exists at: {venv_path}")
        return True
        
    print(f"Creating virtual environment at: {venv_path}")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        print("✓ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return False

def remove_venv():
    venv_path = get_venv_path()
    
    if not venv_exists():
        print("Virtual environment doesn't exist")
        return True
        
    print(f"Removing virtual environment at: {venv_path}")
    try:
        import shutil
        shutil.rmtree(venv_path)
        print("✓ Virtual environment removed successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to remove virtual environment: {e}")
        return False

def install_requirements():
    if not venv_exists():
        print("Virtual environment doesn't exist. Creating it first...")
        if not create_venv():
            return False
    
    requirements_path = get_script_dir() / "requirements.txt"
    if not requirements_path.exists():
        print(f"Requirements file not found: {requirements_path}")
        return False
    
    python_exe = get_venv_python()
    print(f"Installing requirements using: {python_exe}")
    
    try:
        subprocess.check_call([
            str(python_exe), "-m", "pip", "install", 
            "-r", str(requirements_path), "--upgrade"
        ])
        print("✓ Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        return False

def run_in_venv(command):
    if not venv_exists():
        print("Virtual environment doesn't exist")
        return False
    
    python_exe = get_venv_python()
    cmd = [str(python_exe)] + command
    
    try:
        subprocess.check_call(cmd, cwd=get_script_dir())
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return False

def show_info():
    venv_path = get_venv_path()
    python_exe = get_venv_python()
    
    print("Shareify Virtual Environment Info:")
    print(f"  Path: {venv_path}")
    print(f"  Python executable: {python_exe}")
    print(f"  Exists: {'Yes' if venv_exists() else 'No'}")
    
    if venv_exists():
        try:
            result = subprocess.run([str(python_exe), "--version"], 
                                  capture_output=True, text=True)
            print(f"  Python version: {result.stdout.strip()}")
        except Exception:
            print("  Python version: Unknown")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Shareify Virtual Environment Manager")
    parser.add_argument("action", choices=["create", "remove", "install", "info", "run"],
                       help="Action to perform")
    parser.add_argument("command", nargs="*", 
                       help="Command to run (for 'run' action)")
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_venv()
    elif args.action == "remove":
        remove_venv()
    elif args.action == "install":
        install_requirements()
    elif args.action == "info":
        show_info()
    elif args.action == "run":
        if not args.command:
            print("No command specified to run")
            sys.exit(1)
        run_in_venv(args.command)

if __name__ == "__main__":
    main()
