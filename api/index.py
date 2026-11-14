"""Vercel serverless entry point: the FastAPI app from backend/, with a SQLite database in /tmp.

Saved projects live only while the function instance is warm (a public demo). Set DATABASE_URL to a
PostgreSQL URL in the Vercel project settings to keep them permanently.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/hallplan.db")

from app.database.session import Base, engine  # noqa: E402
import app.models.project  # noqa: E402,F401  (registers the tables)
from app.main import app  # noqa: E402,F401

Base.metadata.create_all(engine)
