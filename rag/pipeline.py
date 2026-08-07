"""
Print-free pipeline API for indexing and querying documents.

This module is the programmatic entry point for the RAG engine — CLI and
web layers should call these functions and handle presentation themselves.
"""

from pathlib import Path

from rag.ingestion import extract_text_from_pdf
from rag.chunking import chunk_text
from rag.indexing import build_vector_store_from_pdf, make_document_id
from rag.retrieval import answer_query as retrieve_answer_for_query, retrieve_summary_evidence, build_summary_dict
from rag.evaluation import (
    load_gold_references,
    evaluate_summary_dict,
    load_followup_questions,
    evaluate_followup_questions,
)
from rag.config import SUMMARY_QUERIES
from rag.resources import preload


BASE_DIR = Path(__file__).resolve().parent.parent


def resolve_project_path(path):
    path = Path(path)
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def index_document(pdf_path, document_id=None):
    """
    Extracts, chunks, and indexes a PDF. Returns a structured summary.
    """
    pdf_path = resolve_project_path(pdf_path)
    document_id = document_id or make_document_id(pdf_path)

    extracted_text = extract_text_from_pdf(pdf_path)
    chunks = chunk_text(extracted_text)
    build_vector_store_from_pdf(pdf_path, document_id=document_id)

    return {
        "document_id": document_id,
        "pdf_path": str(pdf_path),
        "source": pdf_path.name,
        "character_count": len(extracted_text),
        "text_preview": extracted_text[:500],
        "chunk_count": len(chunks),
        "first_chunk": {
            "section": chunks[0]["section"],
            "text_preview": chunks[0]["text"][:300],
        } if chunks else None,
    }


def index_documents(pdf_paths, document_id=None):
    """
    Indexes multiple PDFs. Returns a list of per-document summaries.
    """
    pdf_paths = list(pdf_paths)
    if document_id and len(pdf_paths) > 1:
        raise ValueError("document_id can only be used with a single PDF.")

    return [index_document(pdf_path, document_id=document_id) for pdf_path in pdf_paths]


def list_documents():
    """
    Lists indexed documents with their source filename and chunk count.
    """
    from rag.resources import get_vector_store

    stored = get_vector_store().get(include=["metadatas"])
    documents = {}

    for metadata in stored.get("metadatas", []):
        document_id = metadata.get("document_id")
        if not document_id:
            continue
        entry = documents.setdefault(
            document_id,
            {"document_id": document_id, "source": metadata.get("source"), "chunk_count": 0},
        )
        entry["chunk_count"] += 1

    return sorted(documents.values(), key=lambda entry: entry["document_id"])


def delete_document(document_id, pdf_dir=None):
    """
    Removes all indexed chunks for a document and deletes its source PDF.

    Returns a dict with the number of chunks removed (0 if the document
    was not indexed) and whether a PDF file was deleted.
    """
    from rag.config import DATA_DIR
    from rag.indexing import remove_existing_document
    from rag.resources import get_vector_store

    vector_store = get_vector_store()
    existing = vector_store.get(where={"document_id": document_id}, include=["metadatas"])
    removed_count = len(existing.get("ids", []))

    # Resolve the source filename from stored metadata before deleting chunks.
    source = None
    for metadata in existing.get("metadatas", []):
        if metadata.get("source"):
            source = metadata["source"]
            break

    if removed_count:
        remove_existing_document(vector_store, document_id)

    file_deleted = False
    if source:
        pdf_path = Path(pdf_dir or DATA_DIR) / source
        if pdf_path.is_file():
            pdf_path.unlink()
            file_deleted = True

    return {
        "document_id": document_id,
        "removed_chunks": removed_count,
        "file_deleted": file_deleted,
        "source": source,
    }


def answer_question(query, top_k=3, document_ids=None, answer_mode="extractive"):
    """
    Answers a question from evidence retrieved across the selected documents.

    Returns the structured answer dict from retrieval.answer_query, plus
    the applied document filter and answer mode.
    """
    result = retrieve_answer_for_query(
        query,
        top_k=top_k,
        document_id=document_ids,
        answer_mode=answer_mode,
    )
    result["filtered_document_ids"] = list(document_ids) if document_ids else []
    result["answer_mode"] = answer_mode
    return result


def summarize_document(document_ids=None, top_k=3, answer_mode="extractive"):
    """
    Builds the structured problem/method/dataset/results/limitations summary.
    """
    summary_evidence = retrieve_summary_evidence(SUMMARY_QUERIES, top_k=top_k, document_id=document_ids)
    return build_summary_dict(summary_evidence, answer_mode=answer_mode)


def evaluate_against_gold(gold_path, document_ids=None, answer_mode="extractive", top_k=3):
    """
    Runs the optional gold benchmark. Returns metrics per summary field,
    or None if the gold file has no references.
    """
    gold_path = resolve_project_path(gold_path)
    gold_references = load_gold_references(gold_path)
    if not any(gold_references.values()):
        return None

    summary_dict = summarize_document(document_ids=document_ids, top_k=top_k, answer_mode=answer_mode)
    return evaluate_summary_dict(summary_dict, gold_references)


def evaluate_followups_against_gold(gold_path, document_ids=None, answer_mode="extractive", top_k=3):
    """
    Runs the optional follow-up question benchmark. Returns a list of
    per-question results, or None if the gold file has no follow-up questions.
    """
    gold_path = resolve_project_path(gold_path)
    followup_entries = load_followup_questions(gold_path)
    if not followup_entries:
        return None

    def answer_fn(question):
        return answer_question(question, top_k=top_k, document_ids=document_ids, answer_mode=answer_mode)["answer"]

    return evaluate_followup_questions(followup_entries, answer_fn)
