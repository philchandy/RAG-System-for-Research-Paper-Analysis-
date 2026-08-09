import os
import re
from pathlib import Path
from dotenv import load_dotenv
import openai as OpenAI

MISSING_ANSWER = "I cannot find that in the uploaded document."
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

DEFAULT_SYSTEM_MESSAGE = "You answer only from provided evidence and cite chunk IDs."


def call_openai(prompt, model="gpt-4o-mini", system_message=DEFAULT_SYSTEM_MESSAGE):

    load_dotenv(dotenv_path=ENV_PATH)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to final_proj/.env or your environment.")

    client = OpenAI.OpenAI()
    res = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
    )
    return res.choices[0].message.content.strip()

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
            "I cannot find that in the uploaded document.",
            "",
            "Cite chunk IDs for every factual claim using the exact chunk ID in brackets, like [bert_chunk_0010].",
            "Do not use outside knowledge.",
            "Do not guess.",
            "Keep the answer concise and easy to scan.",
            "Use short paragraphs. When presenting multiple distinct ideas, use a numbered or bulleted list with one idea per line.",
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

    valid_chunk_ids = {str(item["chunk_id"]) for item in evidence_items}
    bracketed_values = extract_cited_chunk_ids(normalized_answer)
    cited_chunk_ids = bracketed_values & valid_chunk_ids
    invalid_chunk_citations = {
        value for value in bracketed_values
        if "chunk" in value.lower() and value not in valid_chunk_ids
    }

    return bool(cited_chunk_ids) and not invalid_chunk_citations


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


def generate_answer_by_mode(question, evidence_items, answer_mode="extractive"):
    llm = call_openai if answer_mode == "openai" else None
    return generate_grounded_answer(question, evidence_items, llm=llm)