"""WSGI entry point for PythonAnywhere deployment.

PythonAnywhere WSGI configuration file path should point to this file.
In the PythonAnywhere Web tab, set the WSGI config to import from here.
"""

import os
import sys

# Add project directory to Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment to production
os.environ.setdefault("FLASK_ENV", "production")

from backend.app import create_app

application = create_app("production")
