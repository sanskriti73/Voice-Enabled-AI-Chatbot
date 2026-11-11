"""Validate the FAQ seed file.

The corrected response generator uses the CSV as its single source of truth,
so this script only validates the seed data. Database FAQ duplication was
removed to prevent the CSV and database from diverging.
"""
import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config

if __name__ == "__main__":
    with open(config.FAQ_CSV_PATH, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"question", "answer", "category"}
    if rows and not required.issubset(rows[0]):
        raise ValueError(f"FAQ CSV must contain columns: {sorted(required)}")
    print(f"Validated {len(rows)} FAQ entries.")
