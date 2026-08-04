import torch

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())


from ingestion import extract_text_from_pdf
from chunking import chunk_text
from indexing import build_vector_store_from_pdf
from retrieval import retrieve_summary_evidence, build_summary_dict
from evaluation import load_gold_references, evaluate_summary_dict
from config import SUMMARY_QUERIES, CHROMA_DIR, EMBEDDING_MODEL
from config import DATA_DIR
from pathlib import Path

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    pdf_path = BASE_DIR / "data" / "raw" / "bert.pdf"

    print("\n--- PDF Extraction ---")
    extracted_text = extract_text_from_pdf(pdf_path)
    print("PDF path:", pdf_path)
    print("Extracted character count:", len(extracted_text))
    print("Text preview:")
    print(extracted_text[:500])

    print("\n--- Chunking Test ---")
    chunks = chunk_text(extracted_text)
    print("Chunk count:", len(chunks))
    if chunks:
        print("First chunk preview:")
        print("Section:", chunks[0]["section"])
        print(chunks[0]["text"][:300])

    print("\n--- Vector Store Build ---")
    build_vector_store_from_pdf(pdf_path)

    print("\n--- Retrieval ---")
    summary_evidence = retrieve_summary_evidence(SUMMARY_QUERIES, top_k=3)
    summary_dict = build_summary_dict(summary_evidence)

    for field, payload in summary_evidence.items():
        print(f"\nField: {field}")
        print("Query:", payload["query"])
        for index, chunk in enumerate(payload["retrieved_chunks"], start=1):
            print(f"\nResult {index}:")
            print("Section:", chunk["section"])
            print("Chunk ID:", chunk["chunk_id"])
            print(chunk["evidence"])

    print("\n--- Summary Dict ---")
    for field, payload in summary_dict.items():
        print(f"\n{field.upper()}:")
        print("Query:", payload["query"])
        print("Chunk IDs:", payload["chunk_ids"])
        print("Sections:", payload["sections"])
        print("Evidence count:", len(payload["evidence_snippets"]))

    print("\n--- Gold Evaluation ---")
    gold_references = load_gold_references()
    evaluation = evaluate_summary_dict(summary_dict, gold_references)

    for field, metrics in evaluation.items():
        print(f"\n{field.upper()}:")
        print("Coverage:", metrics["coverage"])
        print("Hallucination:", metrics["hallucination"])
        print("Matched keywords:", metrics["matched_keywords"])

