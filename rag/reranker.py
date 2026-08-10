from rag.resources import get_reranker


def score_with_cross_encoder(query, documents):
    """
    Scores each document's relevance to the query. Returns (document, score) pairs
    in the original input order (unsorted).
    """
    if not documents:
        return []

    reranker = get_reranker()
    pairs = [(query, doc.page_content) for doc in documents]
    scores = reranker.predict(pairs)
    return list(zip(documents, scores))


def cross_encoder_rerank(query, documents, limit):
    scored_documents = score_with_cross_encoder(query, documents)
    ranked_documents = sorted(
        scored_documents,
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [doc for doc, _ in ranked_documents[:limit]]
