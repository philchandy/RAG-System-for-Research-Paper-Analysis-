import re

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from rag.resources import get_vector_store
from rag.reranker import cross_encoder_rerank, score_with_cross_encoder


RRF_K = 60


def make_vector_store():
    """
    Returns the shared Chroma vector store singleton.
    """
    return get_vector_store()


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


def tokenize_for_bm25(text):
    return re.findall(r"[a-z0-9]+", text.lower())


_BM25_CACHE = {}


def make_bm25_cache_key(document_ids, stored_ids):
    """
    Cache key for a document selection. Including the stored chunk ids
    invalidates the cache when a document is re-indexed or removed.
    """
    if isinstance(document_ids, str):
        document_ids = [document_ids]
    id_part = tuple(sorted(document_ids)) if document_ids else ("__all__",)
    return (id_part, len(stored_ids), hash(tuple(sorted(stored_ids))))


def load_bm25_corpus(vector_store, search_filter=None, document_ids=None):
    """
    Loads stored chunks and builds a BM25 index over their tokenized text.
    Results are cached per document selection and invalidated on re-index.
    """
    stored_ids = vector_store.get(where=search_filter, include=[]).get("ids", [])
    cache_key = make_bm25_cache_key(document_ids, stored_ids)

    cached = _BM25_CACHE.get(cache_key)
    if cached is not None:
        return cached

    stored = vector_store.get(where=search_filter, include=["documents", "metadatas"])
    documents = [
        Document(page_content=text, metadata=metadata)
        for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", []))
    ]
    if not documents:
        return None, []

    bm25 = BM25Okapi([tokenize_for_bm25(doc.page_content) for doc in documents])
    _BM25_CACHE.clear()  # keep at most one corpus in memory
    _BM25_CACHE[cache_key] = (bm25, documents)
    return bm25, documents


def bm25_search(bm25, documents, query, k):
    """
    Returns the top-k documents for a query ranked by BM25 score.
    """
    scores = bm25.get_scores(tokenize_for_bm25(query))
    ranked = sorted(range(len(documents)), key=lambda i: scores[i], reverse=True)
    return [documents[i] for i in ranked[:k] if scores[i] > 0]


def retrieve_multi_query(vector_store, queries, k, search_filter=None, document_ids=None):
    search_result_sets = [
        vector_store.similarity_search(query, k=k, filter=search_filter)
        for query in queries
    ]

    bm25, bm25_documents = load_bm25_corpus(
        vector_store, search_filter=search_filter, document_ids=document_ids
    )
    if bm25 is not None:
        search_result_sets.extend(
            bm25_search(bm25, bm25_documents, query, k) for query in queries
        )

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


SECTION_MATCH_BOOST = 0.2


def section_boosted_rerank(query, documents, section_filter, limit):
    """
    Reranks by relevance, preferring section-filter matches without discarding
    non-matching documents.
    """
    scored_documents = score_with_cross_encoder(query, documents)
    scores = [float(score) for _, score in scored_documents]
    lo, hi = min(scores), max(scores)
    span = (hi - lo) or 1.0

    def combined_score(item):
        doc, score = item
        normalized = (float(score) - lo) / span
        if section_matches(doc.metadata.get("section"), section_filter):
            normalized += SECTION_MATCH_BOOST
        return normalized

    ranked_documents = sorted(scored_documents, key=combined_score, reverse=True)

    return [doc for doc, _ in ranked_documents[:limit]]


def make_document_filter(document_ids):
    """
    Builds a Chroma where-filter for one or many document ids.
    """
    if not document_ids:
        return None
    if isinstance(document_ids, str):
        document_ids = [document_ids]
    if len(document_ids) == 1:
        return {"document_id": document_ids[0]}
    return {"document_id": {"$in": list(document_ids)}}


def retrieve_front_matter(vector_store, document_id=None):
    where_filter = make_document_filter(document_id)
    stored = vector_store.get(where=where_filter, include=["documents", "metadatas"])

    front_matter_docs = [
        Document(page_content=text, metadata=metadata)
        for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", []))
        if metadata.get("section") == "Front Matter"
    ]
    return front_matter_docs


HEADLINE_SECTION_TERMS = ["abstract", "summary", "front matter"]


def retrieve_headline_chunks(vector_store, document_id=None):
    """
    Returns every chunk from a paper's abstract/summary.
    """
    where_filter = make_document_filter(document_id)
    stored = vector_store.get(where=where_filter, include=["documents", "metadatas"])

    return [
        Document(page_content=text, metadata=metadata)
        for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", []))
        if section_matches(metadata.get("section"), HEADLINE_SECTION_TERMS)
    ]


def retrieve_metadata_route(vector_store, route, document_id=None):
    if route.section_filter == ["Front Matter"]:
        return retrieve_front_matter(vector_store, document_id=document_id)

    where_filter = make_document_filter(document_id)
    stored = vector_store.get(where=where_filter, include=["documents", "metadatas"])
    results = []

    for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", [])):
        if section_matches(metadata.get("section"), route.section_filter):
            results.append(Document(page_content=text, metadata=metadata))

    return results


def retrieve(route, question, k=5, document_id=None):
    vector_store = make_vector_store()
    # Wide candidate pool for fusion and reranking; final result is trimmed to k.
    # Scales with k so a larger k (e.g. summary fields) actually searches deeper
    # instead of reranking the same fixed-size pool as a smaller k would.
    candidate_limit = max(k * 3, 12) if route.use_vector_search and len(route.queries) > 1 else k

    if not route.use_vector_search:
        return retrieve_metadata_route(vector_store, route, document_id=document_id)[:k]

    search_filter = make_document_filter(document_id)
    results = retrieve_multi_query(
        vector_store,
        route.queries,
        k=candidate_limit,
        search_filter=search_filter,
        document_ids=document_id,
    )

    if route.section_filter:
        seen_chunk_ids = {doc.metadata.get("chunk_id") for doc in results}
        results = results + [
            doc for doc in retrieve_headline_chunks(vector_store, document_id=document_id)
            if doc.metadata.get("chunk_id") not in seen_chunk_ids
        ]

    if not results:
        return []

    if route.use_reranker:
        if route.section_filter:
            results = section_boosted_rerank(question, results, route.section_filter, limit=candidate_limit)
        else:
            results = cross_encoder_rerank(question, results, limit=candidate_limit)
    elif route.section_filter:
        filtered = filter_documents_by_section(results, route.section_filter)
        results = filtered or retrieve_metadata_route(vector_store, route, document_id=document_id) or results

    return results[:k]
