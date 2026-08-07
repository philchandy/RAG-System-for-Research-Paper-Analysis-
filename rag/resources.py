"""
Shared, lazily-initialized singletons for expensive resources.

The embedding model, Chroma vector store, and cross-encoder reranker are
loaded once per process and reused across requests. A web server should
call preload() at startup to pay all model-loading costs before serving.
"""

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder

from config import CHROMA_DIR, EMBEDDING_MODEL, RERANKER_MODEL


_EMBEDDINGS = None
_VECTOR_STORE = None
_RERANKER = None


def get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        _EMBEDDINGS = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return _EMBEDDINGS


def get_vector_store():
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _VECTOR_STORE = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=get_embeddings(),
        )
    return _VECTOR_STORE


def get_reranker():
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(RERANKER_MODEL)
    return _RERANKER


def preload():
    """
    Eagerly loads all models. Call once at server startup.
    """
    get_vector_store()
    get_reranker()
