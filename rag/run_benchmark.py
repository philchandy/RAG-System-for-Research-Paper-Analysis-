import argparse
import logging

from rag.config import BASE_DIR, DATA_DIR, OUTPUTS_DIR
from rag.evaluation import summarize_followup_results
from rag.indexing import make_document_id
from rag.pipeline import evaluate_against_gold, evaluate_followups_against_gold, index_documents


BENCHMARK_PAIRS = [
    (DATA_DIR / "bert.pdf", OUTPUTS_DIR / "bert_gold.md"),
    (DATA_DIR / "optogenetic_rescue.pdf", OUTPUTS_DIR / "optogenetic_rescue_gold.md"),
    (DATA_DIR / "smart_microscopy.pdf", OUTPUTS_DIR / "smart_microscopy_gold.md"),
]

LOG_PATH = BASE_DIR / "log.log"

logger = logging.getLogger("run_benchmark")


def configure_logging():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")

    file_handler = logging.FileHandler(LOG_PATH, mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run gold benchmark evaluation across every paper that has a matching gold file."
    )
    parser.add_argument(
        "--answer-mode",
        choices=["extractive", "openai"],
        default="openai",
        help="Use extractive evidence snippets or OpenAI-generated grounded answers.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of evidence chunks to retrieve per summary field.",
    )
    parser.add_argument(
        "--judge",
        dest="judge_mode",
        choices=["auto", "keyword", "llm"],
        default="auto",
        help=(
            "How to score follow-up answers: 'keyword' uses lightweight keyword "
            "overlap, 'llm' uses an OpenAI judge call, 'auto' (default) uses the "
            "LLM judge when --answer-mode is openai and keyword overlap otherwise."
        ),
    )
    return parser.parse_args()

def print_paper_evaluation(pdf_path, evaluation):
    logger.info(f"\n--- {pdf_path.name} ---")
    if evaluation is None:
        logger.info("No gold references found. Skipping.")
        return

    for field, metrics in evaluation.items():
        logger.info(f"{field}: coverage={metrics['coverage']}, hallucination={metrics['hallucination']}")
        if metrics["matched_keywords"]:
            logger.info(f"  matched_keywords ({len(metrics['matched_keywords'])}): {metrics['matched_keywords']}")
        if metrics.get("reason"):
            logger.info(f"  judge reason: {metrics['reason']}")


def print_paper_followup_evaluation(pdf_path, results):
    logger.info(f"\n--- {pdf_path.name} follow-up questions ---")
    if results is None:
        logger.info("No follow-up questions found. Skipping.")
        return

    for result in results:
        expected = "answer" if result["answerable"] else "refusal"
        status = "correct" if result["correct"] else "WRONG"
        logger.info(f"[{status}] ({expected}) {result['question']}")
        logger.info(f"  generated: {result['generated_answer']}")
        if result["answerable"]:
            logger.info(f"  reference: {result['reference_answer']}")
        if result.get("reason"):
            logger.info(f"  judge reason: {result['reason']}")

    totals = summarize_followup_results(results)
    logger.info(f"Accuracy: {totals['correct']}/{totals['total']} ({totals['accuracy']:.1%})")
    logger.info(f"Hallucination rate: {totals['hallucinated']}/{totals['total']} ({totals['hallucination_rate']:.1%})")


def print_followup_summary(all_followup_results):
    totals = summarize_followup_results(
        [result for results in all_followup_results if results for result in results]
    )

    logger.info("\n--- Follow-up Question Benchmark Summary ---")
    logger.info(f"Questions scored: {totals['total']}")
    if totals["total"]:
        logger.info(f"Accuracy: {totals['correct']}/{totals['total']} ({totals['accuracy']:.1%})")
        logger.info(f"Hallucination rate: {totals['hallucinated']}/{totals['total']} ({totals['hallucination_rate']:.1%})")


def print_summary(all_evaluations):
    total_fields = 0
    covered_fields = 0
    hallucinated_fields = 0

    for evaluation in all_evaluations:
        if evaluation is None:
            continue
        for metrics in evaluation.values():
            total_fields += 1
            if metrics["coverage"] == "hit":
                covered_fields += 1
            if metrics["hallucination"] == "yes":
                hallucinated_fields += 1

    scored_papers = sum(1 for evaluation in all_evaluations if evaluation is not None)

    logger.info("\n--- Benchmark Summary ---")
    logger.info(f"Papers evaluated: {scored_papers}/{len(all_evaluations)}")
    logger.info(f"Fields scored: {total_fields}")
    if total_fields:
        logger.info(f"Coverage rate: {covered_fields}/{total_fields} ({covered_fields / total_fields:.1%})")
        logger.info(f"Hallucination rate: {hallucinated_fields}/{total_fields} ({hallucinated_fields / total_fields:.1%})")


def main():
    configure_logging()
    args = parse_args()

    all_evaluations = []
    all_followup_results = []
    for pdf_path, gold_path in BENCHMARK_PAIRS:
        document_id = make_document_id(pdf_path)
        index_documents([pdf_path], document_id=document_id)

        evaluation = evaluate_against_gold(
            gold_path,
            document_ids=[document_id],
            answer_mode=args.answer_mode,
            top_k=args.top_k,
            judge_mode=args.judge_mode,
        )
        print_paper_evaluation(pdf_path, evaluation)
        all_evaluations.append(evaluation)

        followup_results = evaluate_followups_against_gold(
            gold_path,
            document_ids=[document_id],
            answer_mode=args.answer_mode,
            top_k=args.top_k,
            judge_mode=args.judge_mode,
        )
        print_paper_followup_evaluation(pdf_path, followup_results)
        all_followup_results.append(followup_results)

    print_summary(all_evaluations)
    print_followup_summary(all_followup_results)


if __name__ == "__main__":
    main()
