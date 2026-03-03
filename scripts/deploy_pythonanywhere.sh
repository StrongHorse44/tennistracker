#!/bin/bash
# PythonAnywhere deployment script for CourtTracker
#
# Usage: Run this from a PythonAnywhere Bash console:
#   cd ~/tennistracker && bash scripts/deploy_pythonanywhere.sh
#
# Prerequisites:
#   1. Clone/pull the repo to ~/tennistracker on PythonAnywhere
#   2. Create a virtualenv: mkvirtualenv courttracker --python=python3.10
#   3. Set up .env file (copy from .env.pythonanywhere and fill in values)
#
# PythonAnywhere Web Tab Settings:
#   - Source code:    /home/skipperslipper/tennistracker
#   - Working dir:    /home/skipperslipper/tennistracker
#   - Virtualenv:     /home/skipperslipper/.virtualenvs/courttracker
#   - WSGI config:    Edit to import from wsgi.py (see pythonanywhere_wsgi.py)

set -e

echo "=== CourtTracker PythonAnywhere Deployment ==="

# Detect PythonAnywhere username from home directory
PA_USER=$(basename "$HOME")
PROJECT_DIR="$HOME/tennistracker"

echo "User: $PA_USER"
echo "Project: $PROJECT_DIR"

# Ensure we're in the project directory
cd "$PROJECT_DIR"

# Pull latest code
echo ""
echo "--- Pulling latest code ---"
git pull origin claude/courttracker-player-tracking-qohJC

# Activate virtualenv
echo ""
echo "--- Setting up virtualenv ---"
VENV_DIR="$HOME/.virtualenvs/courttracker"
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Creating virtualenv..."
    python3.10 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
fi

# Install dependencies
echo ""
echo "--- Installing dependencies ---"
pip install --upgrade pip
pip install -r requirements.txt

# Load env vars if .env file exists
if [ -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "--- Loading .env ---"
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Set production environment
export FLASK_ENV=production

# Initialize/migrate database
echo ""
echo "--- Database setup ---"
DB_PATH="$PROJECT_DIR/courttracker.db"
if [ ! -f "$DB_PATH" ]; then
    echo "Creating database..."
    python -c "
from backend.app import create_app
from backend.extensions import db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('Database tables created.')
"
else
    echo "Database exists at $DB_PATH"
fi

# Seed data
echo ""
echo "--- Seeding database ---"
python scripts/seed_database.py

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Next steps:"
echo "  1. Go to PythonAnywhere Web tab"
echo "  2. Set Source code to: $PROJECT_DIR"
echo "  3. Set Virtualenv to: $VENV_DIR"
echo "  4. Edit WSGI config file (see pythonanywhere_wsgi.py for contents)"
echo "  5. Click 'Reload' button"
echo "  6. Visit: https://${PA_USER}.pythonanywhere.com/api/v1/health"
