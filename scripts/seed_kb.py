"""
scripts/seed_kb.py
Loads datasets/faq_seed.csv into the FAQEntry table so the knowledge
base is queryable/editable from the admin dashboard, not just the flat
CSV file used at cold-start by modules/response_generator.py.
 
Usage:
    python scripts/seed_kb.py
"""
 
import csv
import os
import sys
 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
from app import app
from modules.database import db, FAQEntry
import config
 
 
def main():
    with app.app_context():
        db.create_all()
 
        with open(config.FAQ_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                exists = FAQEntry.query.filter_by(question=row["question"]).first()
                if exists:
                    continue
                entry = FAQEntry(
                    question=row["question"],
                    answer=row["answer"],
                    category=row.get("category"),
                )
                db.session.add(entry)
                count += 1
 
            db.session.commit()
            print(f"Seeded {count} new FAQ entries.")
 
 
if __name__ == "__main__":
    main()
 

