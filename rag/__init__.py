"""
RAG engine for research-paper indexing and grounded question answering.

Public API for servers and scripts:

    from rag import preload, index_documents, answer_question
"""

from rag.pipeline import (
    answer_question,
    evaluate_against_gold,
    evaluate_followups_against_gold,
    index_document,
    index_documents,
    list_documents,
    summarize_document,
)
from rag.resources import preload
