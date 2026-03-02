"""PythonAnywhere WSGI configuration.

Copy this ENTIRE file's contents into the WSGI configuration file
on PythonAnywhere's Web tab. The WSGI config file is typically at:
  /var/www/tennisskipperslipper_pythonanywhere_com_wsgi.py

Replace 'tennisskipperslipper' with your actual PythonAnywhere username
if different.
"""

import os
import sys

# === EDIT THIS: your PythonAnywhere username ===
PA_USERNAME = "tennisskipperslipper"

# Project paths
project_home = f"/home/{PA_USERNAME}/tennistracker"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load .env file if it exists
env_path = os.path.join(project_home, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

# Set production environment
os.environ["FLASK_ENV"] = "production"

# Import the app
from backend.app import create_app

application = create_app("production")
