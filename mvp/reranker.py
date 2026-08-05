from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL


_RERANKER = None


def get_reranker():
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(RERANKER_MODEL)
    return _RERANKER


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
