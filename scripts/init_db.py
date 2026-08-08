"""
scripts/init_db.py
One-off utility to (re)create the SQLite database schema from the
SQLAlchemy models defined in modules/database.py.
 
Usage:
    python scripts/init_db.py
"""
 
import sys
import os
 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
from app import app
from modules.database import db
 
 
def main():
    with app.app_context():
        db.create_all()
        print("Database schema created at", app.config["SQLALCHEMY_DATABASE_URI"])
 
 
if __name__ == "__main__":
    main()
 
