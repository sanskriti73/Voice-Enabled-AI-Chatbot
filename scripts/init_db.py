"""Create the SQLite schema."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from modules.database import db

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database schema created.")
