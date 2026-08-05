from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from answer import generate_grounded_answer
from config import CHROMA_DIR, EMBEDDING_MODEL

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

def retrieve_top_k(query, k=5, document_id=None):
    """
    Retrieves the top-k most similar documents from the vector store for a given query.
    """
    # Load the vector store
    vector_store = Chroma(
        persist_directory=CHROMA_DIR, 
        embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    )
    
    search_filter = {"document_id": document_id} if document_id else None

    # Retrieve top-k documents using pure vector similarity.
    return vector_store.similarity_search(query, k=k, filter=search_filter)

def answer_query(user_query, top_k=5, document_id=None):
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

    answer = generate_grounded_answer(user_query, evidence_items)

    return {
        "query": user_query,
        "answer": answer,
        "evidence_snippets": evidence_snippets,
        "chunk_ids": chunk_ids,
        "sections": sections,
        "sources": sources,
        "document_ids": document_ids,
    }


def generate_schema(query, k=3, document_id=None):
    """
    Backward-compatible wrapper for the old fixed-summary MVP path.
    """
    return answer_query(query, top_k=k, document_id=document_id)

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

def build_summary_dict(summary_evidence):
    """
    Builds the high-level summary dictionary used for the MVP.
    """
    summary = {}

    for field, payload in summary_evidence.items():
        document_id = None
        if payload["retrieved_chunks"]:
            document_id = payload["retrieved_chunks"][0].get("document_id")
        summary[field] = answer_query(payload["query"], top_k=len(payload["retrieved_chunks"]), document_id=document_id)

    return summary