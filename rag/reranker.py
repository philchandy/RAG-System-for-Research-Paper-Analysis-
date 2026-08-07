from resources import get_reranker


def cross_encoder_rerank(query, documents, limit):
    if not documents:
        return []

    reranker = get_reranker()
    pairs = [(query, doc.page_content) for doc in documents]
    scores = reranker.predict(pairs)
    ranked_documents = sorted(
        zip(documents, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [doc for doc, _ in ranked_documents[:limit]]
