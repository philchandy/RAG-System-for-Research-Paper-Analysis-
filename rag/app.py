"""
Thin CLI wrapper over the pipeline API in pipeline.py.

All indexing/retrieval logic lives in pipeline.py; this module only
parses arguments and formats returned dicts for the terminal.
"""

import argparse
from pathlib import Path

import torch

from config import DEFAULT_GOLD_PATH
from pipeline import answer_question, evaluate_against_gold, index_documents, summarize_document


def parse_args():
    parser = argparse.ArgumentParser(description="Index a research PDF and query it with retrieved evidence.")
    parser.add_argument(
        "--pdf",
        type=Path,
        nargs="+",
        required=True,
        help="Path(s) to one or more research PDFs to index and query together.",
    )
    parser.add_argument(
        "--query",
        default=None,
        help=(
            "Ask a single question and exit instead of the default flow "
            "(index, print the 5-part summary, then prompt for follow-ups)."
        ),
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of evidence chunks to retrieve.",
    )
    parser.add_argument(
        "--answer-mode",
        choices=["extractive", "openai"],
        default="extractive",
        help="Use extractive evidence snippets or OpenAI-generated grounded answers.",
    )
    parser.add_argument(
        "--document-id",
        help="Optional id for the uploaded document (single --pdf only). Defaults to a slug from each PDF file name.",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run optional benchmark evaluation against manually written gold references.",
    )
    parser.add_argument(
        "--bert-eval",
        dest="evaluate",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--gold-file",
        type=Path,
        default=DEFAULT_GOLD_PATH,
        help="Markdown file containing manually written gold references for benchmark evaluation.",
    )
    return parser.parse_args()


def print_environment():
    print("PyTorch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())


def print_index_report(report):
    print("\n--- PDF Extraction ---")
    print("PDF path:", report["pdf_path"])
    print("Document ID:", report["document_id"])
    print("Extracted character count:", report["character_count"])
    print("Text preview:")
    print(report["text_preview"])

    print("\n--- Chunking ---")
    print("Chunk count:", report["chunk_count"])
    if report["first_chunk"]:
        print("First chunk preview:")
        print("Section:", report["first_chunk"]["section"])
        print(report["first_chunk"]["text_preview"])

    print("\n--- Vector Store Build ---")
    print(f"Indexed document '{report['document_id']}'.")


def print_answer(result, max_evidence=None):
    print("\n--- Query Retrieval ---")
    print("Query:", result["query"])
    if result["filtered_document_ids"]:
        print("Filtered document IDs:", ", ".join(result["filtered_document_ids"]))
    print("Answer mode:", result["answer_mode"])
    print("Answer from retrieved evidence:")
    print(result["answer"])

    evidence_snippets = result["evidence_snippets"]
    if max_evidence is not None:
        evidence_snippets = evidence_snippets[:max_evidence]

    for index, evidence in enumerate(evidence_snippets, start=1):
        print(f"\nEvidence {index}:")
        print("Document ID:", result["document_ids"][index - 1])
        print("Source:", result["sources"][index - 1])
        print("Section:", result["sections"][index - 1])
        print("Chunk ID:", result["chunk_ids"][index - 1])
        print(evidence)


def print_document_summary(summary):
    print("\n--- Document Summary ---")
    for field, result in summary.items():
        print(f"\n[{field.upper()}]")
        print(result["answer"])


def run_interactive_loop(document_ids, top_k, answer_mode):
    print("\n--- Follow-up Questions ---")
    print("Type a question and press Enter. Type 'quit' or 'exit' to stop.")

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not query or query.lower() in {"quit", "exit", "q"}:
            break

        result = answer_question(query, top_k=top_k, document_ids=document_ids, answer_mode=answer_mode)
        print_answer(result, max_evidence=top_k)


def print_evaluation(evaluation, gold_path):
    print("\n--- Optional Gold Benchmark Evaluation ---")
    print("Gold reference file:", gold_path)

    if evaluation is None:
        print("No gold references found. Skipping benchmark evaluation.")
        return

    for field, metrics in evaluation.items():
        print(f"\n{field.upper()}:")
        print("Coverage:", metrics["coverage"])
        print("Hallucination:", metrics["hallucination"])
        print("Matched keywords:", metrics["matched_keywords"])


def main():
    args = parse_args()

    print_environment()

    try:
        reports = index_documents(args.pdf, document_id=args.document_id)
    except ValueError as error:
        raise SystemExit(str(error))

    for report in reports:
        print_index_report(report)

    document_ids = [report["document_id"] for report in reports]

    if args.query:
        result = answer_question(
            args.query,
            top_k=args.top_k,
            document_ids=document_ids,
            answer_mode=args.answer_mode,
        )
        print_answer(result, max_evidence=args.top_k)
    else:
        summary = summarize_document(
            document_ids=document_ids,
            top_k=args.top_k,
            answer_mode=args.answer_mode,
        )
        print_document_summary(summary)
        run_interactive_loop(document_ids, args.top_k, args.answer_mode)

    if args.evaluate:
        evaluation = evaluate_against_gold(
            args.gold_file,
            document_ids=document_ids,
            answer_mode=args.answer_mode,
        )
        print_evaluation(evaluation, args.gold_file)


if __name__ == "__main__":
    main()

