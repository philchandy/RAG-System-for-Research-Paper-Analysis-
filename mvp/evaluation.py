import re
from config import GOLD_PATH

def load_gold_references(gold_path=GOLD_PATH):
    """
    Loads the gold reference bullets grouped by field from the markdown file.
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
    if answer_text.strip().lower() == "not found in provided evidence":
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