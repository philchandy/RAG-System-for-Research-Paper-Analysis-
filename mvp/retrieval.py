from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from answer import call_openai, generate_grounded_answer
from config import CHROMA_DIR, EMBEDDING_MODEL

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

FRONT_MATTER_QUERY_TERMS = [
    "author",
    "authors",
    "wrote",
    "written by",
    "title",
]


def make_vector_store():
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL),
    )


def is_front_matter_query(query):
    normalized_query = query.lower()
    return any(term in normalized_query for term in FRONT_MATTER_QUERY_TERMS)


def retrieve_front_matter(vector_store, document_id=None):
    where_filter = {"document_id": document_id} if document_id else None
    stored = vector_store.get(where=where_filter, include=["documents", "metadatas"])

    for text, metadata in zip(stored.get("documents", []), stored.get("metadatas", [])):
        if metadata.get("section") == "Front Matter":
            return Document(page_content=text, metadata=metadata)

    return None

def retrieve_top_k(query, k=5, document_id=None):
    """
    Retrieves the top-k most similar documents from the vector store for a given query.
    """
    vector_store = make_vector_store()
    
    search_filter = {"document_id": document_id} if document_id else None

    results = vector_store.similarity_search(query, k=k, filter=search_filter)

    if is_front_matter_query(query):
        front_matter = retrieve_front_matter(vector_store, document_id=document_id)
        if front_matter:
            front_matter_id = front_matter.metadata.get("chunk_id")
            results = [
                doc for doc in results
                if doc.metadata.get("chunk_id") != front_matter_id
            ]
            results.insert(0, front_matter)

    return results[:k]

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