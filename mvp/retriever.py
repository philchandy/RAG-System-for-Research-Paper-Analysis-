from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from config import CHROMA_DIR, EMBEDDING_MODEL
from reranker import cross_encoder_rerank


CHROMA_DIR.mkdir(parents=True, exist_ok=True)
RRF_K = 60


def make_vector_store():
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
    )


def rerank_search_results(search_result_sets, limit):
    documents_by_chunk_id = {}
    scores_by_chunk_id = {}

    for result_set in search_result_sets:
        for rank, doc in enumerate(result_set, start=1):
            chunk_id = doc.metadata.get("chunk_id")
            if not chunk_id:
                continue
            documents_by_chunk_id.setdefault(chunk_id, doc)
            scores_by_chunk_id[chunk_id] = scores_by_chunk_id.get(chunk_id, 0) + 1 / (RRF_K + rank)

    ranked_chunk_ids = sorted(
        scores_by_chunk_id,
        key=lambda chunk_id: scores_by_chunk_id[chunk_id],
        reverse=True,
    )

    return [documents_by_chunk_id[chunk_id] for chunk_id in ranked_chunk_ids[:limit]]


def retrieve_multi_query(vector_store, queries, k, search_filter=None):
    search_result_sets = [
        vector_store.similarity_search(query, k=k, filter=search_filter)
        for query in queries
    ]
    return rerank_search_results(search_result_sets, limit=k)


def section_matches(section, section_filter):
    if not section_filter:
        return True

    normalized_section = (section or "").lower()
    return any(term.lower() in normalized_section for term in section_filter)


def filter_documents_by_section(documents, section_filter):
    if not section_filter:
        return documents
    return [doc for doc in documents if section_matches(doc.metadata.get("section"), section_filter)]


def retrieve_front_matter(vector_store, document_id=None):
    where_filter = {"document_id": document_id} if document_id else None
    stored = vector_store.get(where=where_filter, include=["documents", "metadatas"])

    for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", [])):
        if metadata.get("section") == "Front Matter":
            return Document(page_content=text, metadata=metadata)

    return None


def retrieve_metadata_route(vector_store, route, document_id=None):
    if route.section_filter == ["Front Matter"]:
        front_matter = retrieve_front_matter(vector_store, document_id=document_id)
        return [front_matter] if front_matter else []

    where_filter = {"document_id": document_id} if document_id else None
    stored = vector_store.get(where=where_filter, include=["documents", "metadatas"])
    results = []

    for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", [])):
        if section_matches(metadata.get("section"), route.section_filter):
            results.append(Document(page_content=text, metadata=metadata))

    return results


def retrieve(route, question, k=5, document_id=None):
    vector_store = make_vector_store()
    result_limit = max(k, 12) if route.use_vector_search and len(route.queries) > 1 else k

    if not route.use_vector_search:
        return retrieve_metadata_route(vector_store, route, document_id=document_id)[:result_limit]

    search_filter = {"document_id": document_id} if document_id else None
    results = retrieve_multi_query(
        vector_store,
        route.queries,
        k=result_limit,
        search_filter=search_filter,
    )
    unfiltered_results = results
    results = filter_documents_by_section(unfiltered_results, route.section_filter)

    if not results and route.section_filter:
        results = retrieve_metadata_route(vector_store, route, document_id=document_id)

    if not results:
        results = unfiltered_results

    if route.use_reranker:
        results = cross_encoder_rerank(question, results, limit=result_limit)

    return results[:result_limit]
