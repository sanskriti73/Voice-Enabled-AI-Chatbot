"""
utils/logger.py
Central logging configuration for the chatbot application.
Produces two rotating log files under logs/:
  - logs/app.log     all INFO-and-above application activity
  - logs/errors.log  ERROR-and-above only, kept separate for fast triage
"""
 
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
 
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
 
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_formatter = logging.Formatter(_FORMAT)
 
 
def _make_handler(filename: str, level: int) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        LOG_DIR / filename,
        maxBytes=5 * 1024 * 1024,   # 5 MB per file
        backupCount=3,               # app.log.1, app.log.2, app.log.3
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(_formatter)
    return handler
 
 
def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger wired to both log files."""
    logger = logging.getLogger(name)
    if not logger.handlers:  # avoid duplicate handlers on reimport
        logger.setLevel(logging.INFO)
        logger.addHandler(_make_handler("app.log", logging.INFO))
        logger.addHandler(_make_handler("errors.log", logging.ERROR))
    return logger
