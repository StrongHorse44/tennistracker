"""WSGI entry point for production deployment.

Can be used with any WSGI server (gunicorn, uWSGI, etc.):
  gunicorn wsgi:application
"""

import os
import sys

# Add project directory to Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load .env file using python-dotenv (installed via requirements.txt)
from dotenv import load_dotenv

load_dotenv(os.path.join(project_home, ".env"))

# Set environment to production
os.environ.setdefault("FLASK_ENV", "production")

from backend.app import create_app

application = create_app("production")
