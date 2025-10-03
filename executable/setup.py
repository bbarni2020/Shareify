import os
import sys
from setuptools import setup, find_packages
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

def read_requirements():
    req_file = os.path.join(current_dir, 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and (not line.startswith('#'))]
    return []

def get_version():
    try:
        import json
        settings_file = os.path.join(current_dir, 'settings', 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                return settings.get('version', '1.0.0')
    except:
        pass
    return '1.0.0'
setup(name='shareify', version=get_version(), description='Simple file sharing server with web interface', author='Shareify Team', python_requires='>=3.7', packages=find_packages(), include_package_data=True, package_data={'': ['web/*', 'web/assets/*', 'web/assets/**/*', 'settings/*', 'db/*']}, install_requires=read_requirements(), entry_points={'console_scripts': ['shareify=shareify.main:main', 'shareify-launcher=shareify.launcher:main', 'shareify-install=shareify.install:main', 'shareify-update=shareify.update:update']}, classifiers=['Development Status :: 4 - Beta', 'Intended Audience :: End Users/Desktop', 'License :: OSI Approved :: MIT License', 'Programming Language :: Python :: 3', 'Programming Language :: Python :: 3.7', 'Programming Language :: Python :: 3.8', 'Programming Language :: Python :: 3.9', 'Programming Language :: Python :: 3.10', 'Programming Language :: Python :: 3.11'])