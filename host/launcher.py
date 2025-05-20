import subprocess
import os

subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "main.py")], check=True)