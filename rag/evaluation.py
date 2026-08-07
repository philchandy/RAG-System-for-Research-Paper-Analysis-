import re
from answer import MISSING_ANSWER
from config import DEFAULT_GOLD_PATH

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

def evaluate_summary_dict(summary_dict, gold_references):
    """
    Scores each generated summary field against the matching gold field.
    """
    evaluation = {}
    for field_name, generated_field in summary_dict.items():
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

def evaluate_followup_questions(followup_entries, answer_fn):
    """
    Answers each follow-up question with answer_fn(question) -> answer text
    and scores it against its reference. Returns per-question results.
    """
    results = []
    for entry in followup_entries:
        generated_answer = answer_fn(entry["question"])
        score = score_followup_question(entry, generated_answer)
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