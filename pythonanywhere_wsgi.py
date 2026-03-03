"""PythonAnywhere WSGI configuration.

Copy this ENTIRE file's contents into the WSGI configuration file
on PythonAnywhere's Web tab. The WSGI config file is typically at:
  /var/www/tennis_skipperslipper_pythonanywhere_com_wsgi.py

PythonAnywhere converts hyphens to underscores in the WSGI filename.
"""

import os
import sys

# === EDIT THIS: your PythonAnywhere username ===
PA_USERNAME = "skipperslipper"

# Project paths
project_home = f"/home/{PA_USERNAME}/tennistracker"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load .env file using python-dotenv (installed via requirements.txt)
from dotenv import load_dotenv

env_path = os.path.join(project_home, ".env")
load_dotenv(env_path)

# Set production environment (override any .env value)
os.environ["FLASK_ENV"] = "production"

# Import the app
from backend.app import create_app

application = create_app("production")
