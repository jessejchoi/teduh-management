"""
Vercel serverless entry point.
Imports the FastAPI app from the project root.
"""
import sys
from pathlib import Path

# Make dashboard_server importable from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard_server import app  # noqa: F401 — Vercel looks for `app`
