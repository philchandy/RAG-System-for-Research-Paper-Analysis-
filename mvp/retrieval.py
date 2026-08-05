from answer import generate_answer_by_mode
from planner import plan_query
from retriever import retrieve


def route_query(question):
    return plan_query(question)


def generate_search_queries(query):
    """
    Backward-compatible wrapper for callers that only need routed queries.
    """
    route = route_query(query)
    return route.queries


def retrieve_top_k(query, k=5, document_id=None):
    """
    Plans retrieval, executes the route, and returns retrieved chunks.
    """
    route = route_query(query)
    return retrieve(route, query, k=k, document_id=document_id)


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

    answer = generate_answer_by_mode(user_query, evidence_items, answer_mode=answer_mode)

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
