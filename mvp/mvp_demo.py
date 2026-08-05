import argparse
from pathlib import Path

import torch

from ingestion import extract_text_from_pdf
from chunking import chunk_text
from indexing import build_vector_store_from_pdf, make_document_id
from retrieval import generate_schema, retrieve_summary_evidence, build_summary_dict
from evaluation import load_gold_references, evaluate_summary_dict
from config import SUMMARY_QUERIES


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_QUERY = "What are the main contributions of this document?"


def parse_args():
    parser = argparse.ArgumentParser(description="Index a research PDF and query it with retrieved evidence.")
    parser.add_argument(
        "--pdf",
        type=Path,
        required=True,
        help="Path to the uploaded research PDF to index.",
    )
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help="Question to ask against the indexed document.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of evidence chunks to retrieve.",
    )
    parser.add_argument(
        "--document-id",
        help="Optional id for this uploaded document. Defaults to a slug from the PDF file name.",
    )
    parser.add_argument(
        "--bert-eval",
        action="store_true",
        help="Run the old BERT gold-reference evaluation after indexing. Optional benchmark-only path.",
    )
    return parser.parse_args()


def resolve_pdf_path(pdf_path):
    if pdf_path.is_absolute():
        return pdf_path
    return (BASE_DIR / pdf_path).resolve()


def print_environment():
    print("PyTorch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())


def index_uploaded_document(pdf_path, document_id=None):
    pdf_path = resolve_pdf_path(pdf_path)
    document_id = document_id or make_document_id(pdf_path)

    print("\n--- PDF Extraction ---")
    extracted_text = extract_text_from_pdf(pdf_path)
    print("PDF path:", pdf_path)
    print("Document ID:", document_id)
    print("Extracted character count:", len(extracted_text))
    print("Text preview:")
    print(extracted_text[:500])

    print("\n--- Chunking ---")
    chunks = chunk_text(extracted_text)
    print("Chunk count:", len(chunks))
    if chunks:
        print("First chunk preview:")
        print("Section:", chunks[0]["section"])
        print(chunks[0]["text"][:300])

    print("\n--- Vector Store Build ---")
    build_vector_store_from_pdf(pdf_path, document_id=document_id)

    return document_id


def answer_query(query, top_k, document_id=None):
    print("\n--- Query Retrieval ---")
    result = generate_schema(query, k=top_k, document_id=document_id)
    print("Query:", result["query"])
    if document_id:
        print("Filtered document ID:", document_id)
    print("Answer from retrieved evidence:")
    print(result["answer"])

    for index, evidence in enumerate(result["evidence_snippets"], start=1):
        print(f"\nEvidence {index}:")
        print("Document ID:", result["document_ids"][index - 1])
        print("Source:", result["sources"][index - 1])
        print("Section:", result["sections"][index - 1])
        print("Chunk ID:", result["chunk_ids"][index - 1])
        print(evidence)

    return result


def run_bert_evaluation(document_id=None):
    print("\n--- Optional BERT Gold Evaluation ---")
    summary_evidence = retrieve_summary_evidence(SUMMARY_QUERIES, top_k=3, document_id=document_id)
    summary_dict = build_summary_dict(summary_evidence)

    gold_references = load_gold_references()
    evaluation = evaluate_summary_dict(summary_dict, gold_references)

    for field, metrics in evaluation.items():
        print(f"\n{field.upper()}:")
        print("Coverage:", metrics["coverage"])
        print("Hallucination:", metrics["hallucination"])
        print("Matched keywords:", metrics["matched_keywords"])


def main():
    args = parse_args()

    print_environment()
    document_id = index_uploaded_document(args.pdf, document_id=args.document_id)
    answer_query(args.query, args.top_k, document_id=document_id)

    if args.bert_eval:
        run_bert_evaluation(document_id=document_id)

if __name__ == "__main__":
    main()

