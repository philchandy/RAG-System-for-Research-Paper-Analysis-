import re
from rag.answer import MISSING_ANSWER
from rag.config import DEFAULT_GOLD_PATH

def load_gold_references(gold_path=DEFAULT_GOLD_PATH):
    """
    Loads optional benchmark gold-reference bullets grouped by field from markdown.
    """
    field_names = ["problem", "method", "dataset", "results", "limitations"]
    gold_references = {field: [] for field in field_names}

    if not gold_path.exists():
        return gold_references

    current_field = None
    for raw_line in gold_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            heading = line.removeprefix("## ").strip().lower()
            current_field = heading if heading in gold_references else None
            continue

        if current_field and line.startswith("-"):
            gold_references[current_field].append(line.lstrip("- ").strip())

    return gold_references

def normalize_keywords(text):
    """
    Produces a small keyword set from a text span for lightweight overlap scoring.
    """
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_\-]+", text.lower())
    stopwords = {
        "the", "and", "for", "with", "from", "that", "this", "into", "their", "been",
        "prior", "approaches", "approach", "paper", "model", "models", "using", "used",
        "use", "does", "what", "solve", "solve?", "problem", "method", "results",
        "dataset", "datasets", "limitations", "reported", "report",
    }
    return {token for token in tokens if len(token) > 2 and token not in stopwords}

def score_field_against_gold(field_name, generated_field, gold_references):
    """
    Compares a generated field dict against the gold bullets and returns hit/miss plus hallucination.
    """
    gold_bullets = gold_references.get(field_name, [])
    gold_keywords = set()
    for bullet in gold_bullets:
        gold_keywords.update(normalize_keywords(bullet))

    answer_text = generated_field.get("answer", "")
    evidence_text = " ".join(generated_field.get("evidence_snippets", []))
    generated_text = f"{answer_text} {evidence_text}"
    generated_keywords = normalize_keywords(generated_text)

    coverage_hit = bool(gold_keywords & generated_keywords)

    hallucination = False
    if answer_text.strip() == MISSING_ANSWER:
        hallucination = False
    elif gold_keywords and not coverage_hit:
        hallucination = True

    return {
        "coverage": "hit" if coverage_hit else "miss",
        "hallucination": "yes" if hallucination else "no",
        "matched_keywords": sorted(gold_keywords & generated_keywords),
    }

def build_summary_field_judge_prompt(field_name, generated_field, gold_bullets):
    """
    Builds a grading prompt asking an LLM judge to compare a generated
    summary field against its gold reference bullets.
    """
    gold_text = "\n".join(f"- {bullet}" for bullet in gold_bullets)
    answer_text = generated_field.get("answer", "")
    evidence_text = " ".join(generated_field.get("evidence_snippets", []))
    generated_text = answer_text if not evidence_text else f"{answer_text}\n\nEvidence: {evidence_text}"

    return "\n".join([
        "You are grading a RAG system's generated paper-summary field against gold "
        "reference bullet points written by a human from the paper.",
        "",
        f"Field: {field_name}",
        "",
        f"Gold reference bullets:\n{gold_text}",
        "",
        f"Generated field content:\n{generated_text}",
        "",
        "Grade the generated content:",
        "- COVERAGE: hit if it correctly captures the main/primary claim of the gold "
        "bullets (wording can differ, and it's fine to miss secondary details or only "
        "some of several examples/numbers listed in a bullet); miss only if it fails to "
        "reflect the primary claim, is off-topic, contradicts the gold reference, or "
        "declines to answer. Do not grade it miss merely for omitting minor sub-facts "
        "while still getting the main point right.",
        "- HALLUCINATION: yes if the generated content states something that contradicts "
        "the gold reference or is a fabricated/incorrect claim for this field; no "
        "otherwise (an honest refusal is never hallucination).",
        "",
        "Reason through the comparison first, then commit to your verdict based on that "
        "reasoning — don't decide the verdict first and justify it afterward.",
        "Respond in exactly this format:",
        "REASON: one short sentence explaining your reasoning",
        "COVERAGE: hit or miss",
        "HALLUCINATION: yes or no",
    ])


def parse_summary_field_judge_response(response_text):
    """
    Parses the judge's COVERAGE/HALLUCINATION/REASON response into a
    (coverage_hit, hallucination, reason) tuple.
    """
    coverage_match = re.search(r"COVERAGE:\s*(hit|miss)", response_text, re.IGNORECASE)
    hallucination_match = re.search(r"HALLUCINATION:\s*(yes|no)", response_text, re.IGNORECASE)
    reason_match = re.search(r"REASON:\s*(.+)", response_text, re.IGNORECASE)

    coverage_hit = bool(coverage_match) and coverage_match.group(1).lower() == "hit"
    hallucination = bool(hallucination_match) and hallucination_match.group(1).lower() == "yes"
    reason = reason_match.group(1).strip() if reason_match else response_text.strip()

    return coverage_hit, hallucination, reason


def majority_vote(values, tie_value):
    """
    Aggregates boolean judge votes by majority.
    """
    true_count = sum(1 for value in values if value)
    false_count = len(values) - true_count
    if true_count > false_count:
        return True
    if false_count > true_count:
        return False
    return tie_value


def judge_summary_field(field_name, generated_field, gold_bullets, llm_calls):
    """
    Scores one generated summary field using an ensemble of LLM judges
    instead of keyword overlap.
    """
    if not gold_bullets:
        return {"coverage": "miss", "hallucination": "no", "matched_keywords": [], "reason": "No gold reference bullets for this field."}

    if callable(llm_calls):
        llm_calls = [llm_calls]

    prompt = build_summary_field_judge_prompt(field_name, generated_field, gold_bullets)
    votes = [parse_summary_field_judge_response(llm_call(prompt)) for llm_call in llm_calls]

    coverage_hit = majority_vote([vote[0] for vote in votes], tie_value=False)
    hallucination = majority_vote([vote[1] for vote in votes], tie_value=True)
    reasons = [vote[2] for vote in votes]
    agreement = len(set(vote[:2] for vote in votes)) == 1

    return {
        "coverage": "hit" if coverage_hit else "miss",
        "hallucination": "yes" if hallucination else "no",
        "matched_keywords": [],
        "reason": reasons[0] if len(reasons) == 1 else " | ".join(reasons),
        "judge_agreement": agreement,
    }


def evaluate_summary_dict(summary_dict, gold_references, judge_fn=None):
    """
    Scores each generated summary field against the matching gold field.
    Scores with judge_fn(field_name, generated_field, gold_bullets) -> score
    dict when provided, otherwise falls back to the keyword-overlap scorer.
    """
    evaluation = {}
    for field_name, generated_field in summary_dict.items():
        if judge_fn:
            gold_bullets = gold_references.get(field_name, [])
            evaluation[field_name] = judge_fn(field_name, generated_field, gold_bullets)
        else:
            evaluation[field_name] = score_field_against_gold(field_name, generated_field, gold_references)
    return evaluation

def load_followup_questions(gold_path):
    """
    Parses the optional "## follow_up_questions" section into question/reference
    entries, grouped under "Answerable from the paper:" and
    "Not answered in the paper (...):" subheadings.
    """
    entries = []
    if not gold_path.exists():
        return entries

    in_section = False
    answerable = True
    pending_question = None

    for raw_line in gold_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if line.startswith("## "):
            in_section = line.removeprefix("## ").strip().lower() == "follow_up_questions"
            pending_question = None
            continue

        if not in_section or not line:
            continue

        lowered = line.lower()
        if lowered.startswith("answerable from the paper"):
            answerable = True
            continue
        if lowered.startswith("not answered in the paper"):
            answerable = False
            continue

        if line.startswith("- Q:"):
            pending_question = line.removeprefix("- Q:").strip()
            continue

        if line.startswith("A:") and pending_question is not None:
            entries.append({
                "question": pending_question,
                "reference_answer": line.removeprefix("A:").strip(),
                "answerable": answerable,
            })
            pending_question = None

    return entries

def score_followup_question(entry, generated_answer):
    """
    Scores one follow-up question's generated answer against its reference.

    Unanswerable questions are scored correct only if the system refuses
    (MISSING_ANSWER); answerable questions are scored correct on keyword
    overlap with the reference answer, same as the summary-field scoring.
    """
    answer_text = generated_answer.strip()
    refused = answer_text == MISSING_ANSWER

    if not entry["answerable"]:
        return {
            "expected": "refusal",
            "correct": refused,
            "hallucination": "no" if refused else "yes",
            "matched_keywords": [],
        }

    reference_keywords = normalize_keywords(entry["reference_answer"])
    generated_keywords = normalize_keywords(answer_text)
    matched_keywords = reference_keywords & generated_keywords
    coverage_hit = bool(matched_keywords) and not refused

    return {
        "expected": "answer",
        "correct": coverage_hit,
        "hallucination": "no" if coverage_hit or refused else "yes",
        "matched_keywords": sorted(matched_keywords),
    }

def build_followup_judge_prompt(entry, generated_answer):
    """
    Builds a grading prompt asking an LLM judge to compare a generated
    follow-up answer against its gold reference (or refusal expectation).
    """
    if entry["answerable"]:
        expectation = (
            "This question IS answerable from the paper. The reference answer below "
            "was written by a human from the paper's content."
        )
        reference_block = f"Reference answer:\n{entry['reference_answer']}"
    else:
        expectation = (
            "This question is intentionally NOT answerable from the paper. A correct "
            "response declines to answer (e.g. states the information isn't in the "
            "document), even if it also adds true, relevant context."
        )
        reference_block = "Reference answer: N/A (question is unanswerable from the paper)."

    return "\n".join([
        "You are grading a RAG system's answer against a human-written reference for a benchmark.",
        expectation,
        "",
        f"Question:\n{entry['question']}",
        "",
        reference_block,
        "",
        f"Generated answer:\n{generated_answer}",
        "",
        "Grade the generated answer:",
        "- CORRECT: for answerable questions, it conveys the same core facts as the "
        "reference (wording, units, or extra detail can differ). For unanswerable "
        "questions, it declines to answer instead of guessing.",
        "- HALLUCINATION: the generated answer states a specific fact that is wrong or "
        "unsupported (for unanswerable questions, hallucination means it fabricated an "
        "answer instead of declining).",
        "",
        "Reason through the comparison first, then commit to your verdict based on that "
        "reasoning — don't decide the verdict first and justify it afterward.",
        "Respond in exactly this format:",
        "REASON: one short sentence explaining your reasoning",
        "VERDICT: correct or incorrect",
        "HALLUCINATION: yes or no",
    ])


def parse_followup_judge_response(response_text):
    """
    Parses the judge's VERDICT/HALLUCINATION/REASON response into a (correct,
    hallucination, reason) tuple.
    """
    verdict_match = re.search(r"VERDICT:\s*(correct|incorrect)", response_text, re.IGNORECASE)
    hallucination_match = re.search(r"HALLUCINATION:\s*(yes|no)", response_text, re.IGNORECASE)
    reason_match = re.search(r"REASON:\s*(.+)", response_text, re.IGNORECASE)

    correct = bool(verdict_match) and verdict_match.group(1).lower() == "correct"
    hallucination = bool(hallucination_match) and hallucination_match.group(1).lower() == "yes"
    reason = reason_match.group(1).strip() if reason_match else response_text.strip()

    return correct, hallucination, reason


def judge_followup_answer(entry, generated_answer, llm_calls):
    """
    Scores one follow-up question's generated answer using an ensemble of
    LLM judges instead of keyword overlap.
    """
    if callable(llm_calls):
        llm_calls = [llm_calls]

    prompt = build_followup_judge_prompt(entry, generated_answer)
    votes = [parse_followup_judge_response(llm_call(prompt)) for llm_call in llm_calls]

    correct = majority_vote([vote[0] for vote in votes], tie_value=False)
    hallucination = majority_vote([vote[1] for vote in votes], tie_value=True)
    reasons = [vote[2] for vote in votes]
    agreement = len(set(vote[:2] for vote in votes)) == 1

    return {
        "expected": "answer" if entry["answerable"] else "refusal",
        "correct": correct,
        "hallucination": "yes" if hallucination else "no",
        "matched_keywords": [],
        "reason": reasons[0] if len(reasons) == 1 else " | ".join(reasons),
        "judge_agreement": agreement,
    }


def evaluate_followup_questions(followup_entries, answer_fn, judge_fn=None):
    """
    Answers each follow-up question with answer_fn(question) -> answer text
    and scores it against its reference. Scores with judge_fn(entry,
    generated_answer) -> score dict when provided, otherwise falls back to
    the keyword-overlap scorer. Returns per-question results.
    """
    results = []
    for entry in followup_entries:
        generated_answer = answer_fn(entry["question"])
        score = judge_fn(entry, generated_answer) if judge_fn else score_followup_question(entry, generated_answer)
        results.append({
            "question": entry["question"],
            "reference_answer": entry["reference_answer"],
            "answerable": entry["answerable"],
            "generated_answer": generated_answer,
            **score,
        })
    return results

def summarize_followup_results(results):
    """
    Aggregates per-question follow-up results into overall accuracy/hallucination rates.
    """
    total = len(results)
    correct = sum(1 for result in results if result["correct"])
    hallucinated = sum(1 for result in results if result["hallucination"] == "yes")

    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
        "hallucinated": hallucinated,
        "hallucination_rate": hallucinated / total if total else 0.0,
    }