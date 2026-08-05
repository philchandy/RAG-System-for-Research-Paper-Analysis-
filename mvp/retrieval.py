from enum import Enum

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder
from answer import call_openai, generate_grounded_answer
from config import CHROMA_DIR, EMBEDDING_MODEL, RERANKER_MODEL

CHROMA_DIR.mkdir(parents=True, exist_ok=True)


class Intent(Enum):
    SUMMARY = "summary"
    METHODS = "methods"
    LIMITATIONS = "limitations"
    APPLICATIONS = "applications"
    COMPARE = "compare"
    AUTHOR = "author"
    SECTION = "section"
    UNKNOWN = "unknown"

METHOD_QUERY_TERMS = ["methods", "approaches", "framework", "architecture", "modules"]
INTENT_QUERY_TERMS = {
    Intent.SUMMARY: ["summary", "main ideas", "contributions", "findings", "overview"],
    Intent.METHODS: METHOD_QUERY_TERMS,
    Intent.LIMITATIONS: ["limitations", "challenges", "failures", "weaknesses", "future work"],
    Intent.APPLICATIONS: ["applications", "use cases", "tasks", "domains", "practical uses"],
    Intent.COMPARE: ["comparison", "differences", "advantages", "tradeoffs", "versus"],
    Intent.AUTHOR: ["authors", "title", "front matter", "paper header", "affiliations"],
    Intent.SECTION: ["section", "heading", "part", "topic", "outline"],
    Intent.UNKNOWN: ["summary", "main ideas", "methods", "findings", "limitations"],
}
RRF_K = 60
_RERANKER = None


def make_vector_store():
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
    )


def get_reranker():
    global _RERANKER
    if _RERANKER is None:
        _RERANKER = CrossEncoder(RERANKER_MODEL)
    return _RERANKER


def classify_intent(query):
    normalized_query = query.lower()

    if any(term in normalized_query for term in ["author", "authors", "wrote", "written by", "title"]):
        return Intent.AUTHOR
    if any(term in normalized_query for term in ["compare", "comparison", "versus", "vs", "difference", "different"]):
        return Intent.COMPARE
    if any(term in normalized_query for term in ["limitation", "limitations", "challenge", "challenges", "fail", "failure", "weakness"]):
        return Intent.LIMITATIONS
    if any(term in normalized_query for term in ["application", "applications", "use case", "use cases", "used for", "where is"]):
        return Intent.APPLICATIONS
    if any(term in normalized_query for term in ["method", "methods", "approach", "approaches", "framework", "architecture", "module", "modules"]):
        return Intent.METHODS
    if any(term in normalized_query for term in ["section", "chapter", "part", "where does", "which section"]):
        return Intent.SECTION
    if any(term in normalized_query for term in ["summarize", "summary", "overview", "main", "overall", "contribution", "contributions"]):
        return Intent.SUMMARY

    return Intent.UNKNOWN


def append_unique_documents(target, documents):
    existing_chunk_ids = {doc.metadata.get("chunk_id") for doc in target}
    for doc in documents:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id in existing_chunk_ids:
            continue
        target.append(doc)
        existing_chunk_ids.add(chunk_id)


def build_queries(intent, question):
    """
    Builds five vector-search queries for the detected user intent.
    """
    query_terms = INTENT_QUERY_TERMS[intent]
    if intent == Intent.UNKNOWN:
        return [question] + query_terms[:4]
    return query_terms[:5]


def generate_search_queries(query):
    """
    Backward-compatible wrapper for callers that only need routed queries.
    """
    return build_queries(classify_intent(query), query)


def rerank_search_results(search_result_sets, limit):
    """
    Merges duplicate chunks and reranks with reciprocal-rank fusion.
    """
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


def retrieve_front_matter(vector_store, document_id=None):
    where_filter = {"document_id": document_id} if document_id else None
    stored = vector_store.get(where=where_filter, include=["documents", "metadatas"])

    for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", [])):
        if metadata.get("section") == "Front Matter":
            return Document(page_content=text, metadata=metadata)

    return None

def retrieve_top_k(query, k=5, document_id=None):
    """
    Retrieves chunks using query routing, multi-query search, merge, and reranking.
    """
    vector_store = make_vector_store()
    
    search_filter = {"document_id": document_id} if document_id else None

    intent = classify_intent(query)
    search_queries = build_queries(intent, query)
    result_limit = max(k, 12) if len(search_queries) > 1 else k
    results = retrieve_multi_query(
        vector_store,
        search_queries,
        k=result_limit,
        search_filter=search_filter,
    )
    results = cross_encoder_rerank(query, results, limit=result_limit)

    if intent == Intent.AUTHOR:
        front_matter = retrieve_front_matter(vector_store, document_id=document_id)
        if front_matter:
            front_matter_id = front_matter.metadata.get("chunk_id")
            results = [
                doc for doc in results
                if doc.metadata.get("chunk_id") != front_matter_id
            ]
            results.insert(0, front_matter)

    return results[:result_limit]

def answer_query(user_query, top_k=5, document_id=None, answer_mode="extractive"):
    """
    Answers a user query from retrieved evidence in the vector store.
    """
    results = retrieve_top_k(user_query, k=top_k, document_id=document_id)

    evidence_snippets = []
    chunk_ids = []
    sections = []
    sources = []
    document_ids = []
    evidence_items = []

    for index, doc in enumerate(results, start=1):
        chunk_id = doc.metadata.get("chunk_id") or f"retrieved_{index}"
        section = doc.metadata.get("section")
        source = doc.metadata.get("source")
        document_id = doc.metadata.get("document_id")

        evidence_snippets.append(doc.page_content[:400])
        chunk_ids.append(chunk_id)
        sections.append(section)
        sources.append(source)
        document_ids.append(document_id)
        evidence_items.append(
            {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source": source,
                "section": section,
                "text": doc.page_content,
            }
        )

    llm = call_openai if answer_mode == "openai" else None
    answer = generate_grounded_answer(user_query, evidence_items, llm=llm)

    return {
        "query": user_query,
        "answer": answer,
        "evidence_snippets": evidence_snippets,
        "chunk_ids": chunk_ids,
        "sections": sections,
        "sources": sources,
        "document_ids": document_ids,
    }


def generate_schema(query, k=3, document_id=None, answer_mode="extractive"):
    """
    Backward-compatible wrapper for the old fixed-summary MVP path.
    """
    return answer_query(query, top_k=k, document_id=document_id, answer_mode=answer_mode)

def retrieve_summary_evidence(summary_queries, top_k=3, document_id=None):
    """
    Retrieves top chunks for each fixed summary query and returns a structured dict.
    """
    summary_evidence = {}

    for field, query in summary_queries.items():
        retrieved_docs = retrieve_top_k(query, k=top_k, document_id=document_id)
        summary_evidence[field] = {
            "query": query,
            "retrieved_chunks": [
                {
                    "chunk_id": doc.metadata.get("chunk_id"),
                    "document_id": doc.metadata.get("document_id"),
                    "source": doc.metadata.get("source"),
                    "section": doc.metadata.get("section"),
                    "evidence": doc.page_content[:400],
                }
                for doc in retrieved_docs
            ],
        }

    return summary_evidence

def build_summary_dict(summary_evidence, answer_mode="extractive"):
    """
    Builds the high-level summary dictionary used for the MVP.
    """
    summary = {}

    for field, payload in summary_evidence.items():
        document_id = None
        if payload["retrieved_chunks"]:
            document_id = payload["retrieved_chunks"][0].get("document_id")
        summary[field] = answer_query(
            payload["query"],
            top_k=len(payload["retrieved_chunks"]),
            document_id=document_id,
            answer_mode=answer_mode,
        )

    return summary