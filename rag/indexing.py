from rag.ingestion import extract_text_from_pdf
from rag.chunking import chunk_text

from langchain_core.documents import Document

from pathlib import Path
import re

from rag.resources import get_vector_store


def make_document_id(pdf_path):
    """
    Creates a stable document id from the uploaded file name.
    """
    stem = Path(pdf_path).stem.lower()
    document_id = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return document_id or "uploaded-document"


def remove_existing_document(vector_store, document_id):
    """
    Removes prior chunks for the same document id before re-indexing it.
    """
    existing = vector_store.get(where={"document_id": document_id})
    existing_ids = existing.get("ids", [])
    if existing_ids:
        vector_store.delete(ids=existing_ids)


def build_vector_store_from_pdf(pdf_path, document_id=None):
    """
    Extracts text from a PDF, chunks it, and builds a vector store using Chroma.
    """
    pdf_path = Path(pdf_path)
    document_id = document_id or make_document_id(pdf_path)

    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Chunk the text
    chunks = chunk_text(text)
    
    # Create Document objects
    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "document_id": document_id,
                "source": pdf_path.name,
                "chunk_id": f"{document_id}_chunk_{index:04d}",
                "section": chunk["section"],
            },
        )
        for index, chunk in enumerate(chunks, start=1)
    ]

    vector_store = get_vector_store()
    remove_existing_document(vector_store, document_id)
    vector_store.add_documents(documents)

    return document_id