"""
Server-only configuration. Engine config stays in rag/config.py.
"""

import os

from rag.config import DATA_DIR


UPLOAD_DIR = DATA_DIR  # uploaded PDFs land next to the existing raw papers
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}

# Comma-separated origins allowed to call this API from a browser.
# Defaults cover common local dev frontends (Vite, CRA/Next).
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
