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
from fastapi.middleware.cors import CORSMiddleware

from rag import answer_question, delete_document, index_document, list_documents, preload, summarize_document
from server.schemas import (
    DeleteResponse,
    DocumentListResponse,
    QueryRequest,
    QueryResponse,
    SummarizeRequest,
    SummarizeResponse,
    UploadResponse,
)
from server.settings import ALLOWED_CONTENT_TYPES, CORS_ORIGINS, MAX_UPLOAD_BYTES, UPLOAD_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load embedding model, vector store, and reranker once before serving.
    await anyio.to_thread.run_sync(preload)
    yield


app = FastAPI(title="Research Paper RAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """
    Answers a question from evidence retrieved across the selected documents.
    """
    def run_query():
        return answer_question(
            request.question,
            top_k=request.top_k,
            document_ids=request.document_ids,
            answer_mode=request.answer_mode,
        )

    try:
        result = await anyio.to_thread.run_sync(run_query)
    except RuntimeError as error:
        # e.g. answer_mode=openai without OPENAI_API_KEY configured
        raise HTTPException(status_code=503, detail=str(error))

    return QueryResponse(
        question=result["query"],
        answer=result["answer"],
        answer_mode=result["answer_mode"],
        filtered_document_ids=result["filtered_document_ids"],
        evidence=build_evidence_items(result),
    )


def build_evidence_items(result):
    """
    Zips the pipeline's parallel evidence lists into structured items.
    """
    return [
        {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "source": source,
            "section": section,
            "text": text,
        }
        for chunk_id, document_id, source, section, text in zip(
            result["chunk_ids"],
            result["document_ids"],
            result["sources"],
            result["sections"],
            result["evidence_snippets"],
        )
    ]


@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """
    Builds the five-part paper summary (problem, method, dataset, results,
    limitations) with supporting evidence for the selected documents.
    """
    def run_summary():
        return summarize_document(
            document_ids=request.document_ids,
            top_k=request.top_k,
            answer_mode=request.answer_mode,
        )

    try:
        summary_dict = await anyio.to_thread.run_sync(run_summary)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error))

    summary = {
        field: {
            "question": result["query"],
            "answer": result["answer"],
            "evidence": build_evidence_items(result),
        }
        for field, result in summary_dict.items()
    }

    return SummarizeResponse(
        answer_mode=request.answer_mode,
        filtered_document_ids=request.document_ids or [],
        summary=summary,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
