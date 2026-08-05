import re


MISSING_ANSWER = "I cannot find that in the uploaded document."


def format_evidence_for_prompt(evidence_items):
    """
    Formats retrieved chunks for the grounded answer prompt.
    """
    formatted_chunks = []

    for item in evidence_items:
        formatted_chunks.append(
            "\n".join(
                [
                    f"[chunk_id: {item['chunk_id']}]",
                    f"Section: {item.get('section') or 'unknown'}",
                    f"Source: {item.get('source') or 'unknown'}",
                    item["text"],
                ]
            )
        )

    return "\n\n".join(formatted_chunks)


def build_grounded_answer_prompt(question, evidence_items):
    """
    Builds the prompt used by an LLM answer generation layer.
    """
    evidence_text = format_evidence_for_prompt(evidence_items)

    return "\n".join(
        [
            "You are answering questions about an uploaded document.",
            "",
            "Answer the question using only the provided evidence.",
            "If the evidence does not contain the answer, say:",
            f'"{MISSING_ANSWER}"',
            "",
            "Cite chunk IDs for every factual claim using [chunk_id].",
            "Do not use outside knowledge.",
            "Do not guess.",
            "",
            "Question:",
            question,
            "",
            "Evidence:",
            evidence_text,
            "",
            "Answer:",
        ]
    )


def extract_cited_chunk_ids(answer_text):
    """
    Extracts bracketed chunk citations from a generated answer.
    """
    return set(re.findall(r"\[([^\]]+)\]", answer_text))


def validate_chunk_citations(answer_text, evidence_items):
    """
    Ensures generated citations refer only to chunks provided as evidence.
    """
    normalized_answer = answer_text.strip()
    if normalized_answer == MISSING_ANSWER:
        return True

    cited_chunk_ids = extract_cited_chunk_ids(normalized_answer)
    if not cited_chunk_ids:
        return False

    valid_chunk_ids = {str(item["chunk_id"]) for item in evidence_items}
    return cited_chunk_ids <= valid_chunk_ids


def generate_extractive_answer(evidence_items):
    """
    Provides a no-LLM fallback by returning the strongest retrieved evidence with a citation.
    """
    if not evidence_items:
        return MISSING_ANSWER

    top_evidence = evidence_items[0]
    text = top_evidence["text"].strip()
    if not text:
        return MISSING_ANSWER

    return f"The retrieved evidence says: {text} [{top_evidence['chunk_id']}]"


def generate_grounded_answer(question, evidence_items, llm=None):
    """
    Generates a grounded answer from retrieved chunks.

    Pass an LLM callable later that accepts a prompt string and returns answer text.
    Without an LLM callable, this keeps the MVP extractive and cited.
    """
    if not evidence_items:
        return MISSING_ANSWER

    if llm is None:
        return generate_extractive_answer(evidence_items)

    prompt = build_grounded_answer_prompt(question, evidence_items)
    answer = str(llm(prompt)).strip()

    if not answer:
        return MISSING_ANSWER

    if not validate_chunk_citations(answer, evidence_items):
        return MISSING_ANSWER

    return answer