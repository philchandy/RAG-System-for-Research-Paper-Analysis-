"""
FastAPI backend for the RAG engine.

Run from final_project/:

    uv run uvicorn server.main:app --reload
"""

import re
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
from fastapi import FastAPI, HTTPException, UploadFile

from rag import delete_document, index_document, list_documents, preload
from server.schemas import DeleteResponse, DocumentListResponse, UploadResponse
from server.settings import ALLOWED_CONTENT_TYPES, MAX_UPLOAD_BYTES, UPLOAD_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load embedding model, vector store, and reranker once before serving.
    await anyio.to_thread.run_sync(preload)
    yield


app = FastAPI(title="Research Paper RAG API", lifespan=lifespan)


def safe_pdf_filename(filename):
    """
    Normalizes an uploaded filename to a safe PDF name.
    """
    stem = Path(filename or "uploaded-document").stem
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-.") or "uploaded-document"
    return f"{stem}.pdf"


def save_upload(upload: UploadFile) -> Path:
    destination = UPLOAD_DIR / safe_pdf_filename(upload.filename)
    size = 0
    with destination.open("wb") as output:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                output.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="PDF exceeds maximum upload size.")
            output.write(chunk)
    if size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return destination


@app.post("/documents", response_model=UploadResponse, status_code=201)
async def upload_document(file: UploadFile) -> UploadResponse:
    """
    Uploads a PDF, indexes it (ingest -> chunk -> embed), and returns chunk stats.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported.")

    pdf_path = save_upload(file)

    try:
        # Indexing is CPU-bound and takes seconds; run it off the event loop
        # so the server stays responsive to other requests.
        report = await anyio.to_thread.run_sync(index_document, pdf_path)
    except Exception as error:
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Failed to index PDF: {error}")

    return UploadResponse(status="indexed", report=report)


@app.get("/documents", response_model=DocumentListResponse)
async def get_documents() -> DocumentListResponse:
    """
    Lists indexed documents with source filename and chunk counts.
    """
    documents = await anyio.to_thread.run_sync(list_documents)
    return DocumentListResponse(documents=documents)


@app.delete("/documents/{document_id}", response_model=DeleteResponse)
async def remove_document(document_id: str) -> DeleteResponse:
    """
    Deletes all indexed chunks for a document id and its uploaded PDF file.
    """
    result = await anyio.to_thread.run_sync(delete_document, document_id)
    if result["removed_chunks"] == 0 and not result["file_deleted"]:
        raise HTTPException(status_code=404, detail=f"No indexed document with id '{document_id}'.")
    return DeleteResponse(**result)


@app.get("/health")
async def health():
    return {"status": "ok"}
