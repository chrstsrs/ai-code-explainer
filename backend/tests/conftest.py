# backend/tests/conftest.py
import os
import sys
from pathlib import Path
import pytest

# Ensure /srv/backend/app (repo: backend/app) is on sys.path so "import server" works
THIS_FILE = Path(__file__).resolve()
BACKEND_ROOT = THIS_FILE.parents[1]     # backend/
APP_DIR = BACKEND_ROOT / "app"          # backend/app
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Point pytest-django at your dev settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings.dev")

@pytest.fixture(autouse=True)
def _enable_db_access_for_all_tests(db):
    """Allow DB access in all tests in this folder."""
    pass

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()
