"""
Server-only configuration. Engine config stays in rag/config.py.
"""

from pathlib import Path

from rag.config import DATA_DIR


UPLOAD_DIR = DATA_DIR  # uploaded PDFs land next to the existing raw papers
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
