from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config import CHROMA_DIR, EMBEDDING_MODEL

CHROMA_DIR.mkdir(parents=True, exist_ok=True)

def infer_preferred_sections(query):
    """
    Returns section names to prefer for simple query types.
    """
    normalized_query = query.lower()

    if any(keyword in normalized_query for keyword in ["problem", "motivation", "limitation", "why"]):
        return ["Abstract", "1 Introduction", "Introduction"]

    if any(keyword in normalized_query for keyword in ["method", "approach", "model", "architecture"]):
        return ["Abstract", "3 BERT", "2.1 Input/Output Representations", "3.1 Pre-training BERT"]

    if any(keyword in normalized_query for keyword in ["result", "performance", "dataset", "benchmark", "evaluation"]):
        return ["4 Experiments", "Abstract", "4.1 GLUE", "4.2 SQuAD v1.1", "4.3 SQuAD v2.0"]

    return []

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

    # Retrieve top-k documents
    results = vector_store.similarity_search(query, k=max(k * 4, 10), filter=search_filter)

    preferred_sections = infer_preferred_sections(query)
    if preferred_sections:
        preferred_lookup = {section: index for index, section in enumerate(preferred_sections)}
        results.sort(
            key=lambda doc: (
                preferred_lookup.get(doc.metadata.get("section"), len(preferred_lookup)),
            )
        )
    
    return results[:k]

def generate_schema(query, k=3, document_id=None):
    """
    Generates a grounded schema dictionary from retrieved evidence.
    """
    results = retrieve_top_k(query, k=k, document_id=document_id)

    evidence_snippets = []
    chunk_ids = []
    sections = []
    sources = []
    document_ids = []

    for doc in results:
        evidence_snippets.append(doc.page_content[:400])
        chunk_ids.append(doc.metadata.get("chunk_id"))
        sections.append(doc.metadata.get("section"))
        sources.append(doc.metadata.get("source"))
        document_ids.append(doc.metadata.get("document_id"))

    normalized_query = query.lower()
    if any(keyword in normalized_query for keyword in ["problem", "motivation", "limitation", "why"]):
        answer = evidence_snippets[0] if evidence_snippets else "Not found in provided evidence"
    elif any(keyword in normalized_query for keyword in ["method", "approach", "model", "architecture"]):
        answer = evidence_snippets[0] if evidence_snippets else "Not found in provided evidence"
    elif any(keyword in normalized_query for keyword in ["result", "performance", "dataset", "benchmark", "evaluation"]):
        answer = evidence_snippets[0] if evidence_snippets else "Not found in provided evidence"
    else:
        answer = evidence_snippets[0] if evidence_snippets else "Not found in provided evidence"

    return {
        "query": query,
        "answer": answer,
        "evidence_snippets": evidence_snippets,
        "chunk_ids": chunk_ids,
        "sections": sections,
        "sources": sources,
        "document_ids": document_ids,
    }

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
        summary[field] = generate_schema(payload["query"], k=len(payload["retrieved_chunks"]), document_id=document_id)

    return summary