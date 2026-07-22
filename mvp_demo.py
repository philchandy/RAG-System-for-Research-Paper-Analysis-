from pathlib import Path
import shutil
import re
import pandas as pd

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from PyPDF2 import PdfReader

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(exist_ok=True)

CHROMA_DIR = Path("data/chroma")
CHROMA_DIR.mkdir(exist_ok=True)


NUMBERED_SECTION_PATTERN = re.compile(r"^\d+(?:\.\d+)*\s+[A-Z].+")
NAMED_SECTION_HEADERS = {
    "abstract",
    "introduction",
    "related work",
    "experiments",
    "conclusion",
}


def normalize_pdf_text(text):
    """
    Normalizes PDF-extracted text so retrieval chunks keep coherent phrases.
    """
    text = text.replace("-\n", "")
    text = text.replace("\r\n", "\n")
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def trim_back_matter(text):
    """
    Removes references and appendix content from extracted paper text.
    """
    cut_patterns = [
        r"\nReferences\b",
        r"\nREFERENCES\b",
        r"\nAppendix\b",
        r"\nAPPENDIX\b",
        r"\nAppendix for",
    ]

    cut_index = len(text)
    for pattern in cut_patterns:
        match = re.search(pattern, text)
        if match:
            cut_index = min(cut_index, match.start())

    return text[:cut_index].strip()


def is_section_header(line):
    """
    Heuristic detector for major paper section headers.
    """
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > 80:
        return False

    lowercase = stripped.lower()
    if lowercase in NAMED_SECTION_HEADERS:
        return True

    return bool(NUMBERED_SECTION_PATTERN.match(stripped))


def split_into_sections(text):
    """
    Splits extracted paper text into named sections before chunking.
    """
    lines = [line.strip() for line in text.splitlines()]
    sections = []
    current_title = "Front Matter"
    current_lines = []

    for line in lines:
        if not line:
            if current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue

        if is_section_header(line):
            if current_lines:
                sections.append({
                    "section": current_title,
                    "text": "\n".join(current_lines).strip(),
                })
            current_title = line
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        sections.append({
            "section": current_title,
            "text": "\n".join(current_lines).strip(),
        })

    cleaned_sections = []
    for section in sections:
        if section["section"] == "Front Matter":
            continue
        normalized = normalize_pdf_text(section["text"])
        if normalized:
            cleaned_sections.append({
                "section": section["section"],
                "text": normalized,
            })

    return cleaned_sections


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


def split_long_unit(unit, chunk_size):
    """
    Splits a long paragraph into sentence groups that fit within chunk_size.
    """
    if len(unit) <= chunk_size:
        return [unit]

    sentences = re.split(r"(?<=[.!?])\s+", unit)
    pieces = []
    current = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        candidate = " ".join(current + [sentence]).strip()
        if current and len(candidate) > chunk_size:
            pieces.append(" ".join(current).strip())
            current = [sentence]
        else:
            current.append(sentence)

    if current:
        pieces.append(" ".join(current).strip())

    final_pieces = []
    for piece in pieces:
        if len(piece) <= chunk_size:
            final_pieces.append(piece)
            continue

        start = 0
        while start < len(piece):
            end = min(start + chunk_size, len(piece))
            final_pieces.append(piece[start:end].strip())
            start = end

    return final_pieces

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyPDF2.
    """
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return trim_back_matter(text)

def chunk_text(text, chunk_size=1200, overlap=150):
    """
    Splits text into paragraph-aware chunks with overlapping trailing context.
    """
    chunks = []
    sections = split_into_sections(text)

    for section in sections:
        paragraphs = [paragraph.strip() for paragraph in section["text"].split("\n\n") if paragraph.strip()]
        units = []

        for paragraph in paragraphs:
            units.extend(split_long_unit(paragraph, chunk_size))

        current_units = []

        for unit in units:
            candidate = "\n\n".join(current_units + [unit]).strip()
            if current_units and len(candidate) > chunk_size:
                chunk = "\n\n".join(current_units).strip()
                chunks.append({"section": section["section"], "text": chunk})

                overlap_units = []
                overlap_length = 0
                for previous_unit in reversed(current_units):
                    overlap_units.insert(0, previous_unit)
                    overlap_length += len(previous_unit)
                    if overlap_length >= overlap:
                        break

                current_units = overlap_units

                candidate = "\n\n".join(current_units + [unit]).strip()
                if current_units and len(candidate) > chunk_size:
                    current_units = [unit]
                else:
                    current_units.append(unit)
            else:
                current_units.append(unit)

        if current_units:
            chunks.append({
                "section": section["section"],
                "text": "\n\n".join(current_units).strip(),
            })

    return chunks

def build_vector_store_from_pdf(pdf_path):
    """
    Extracts text from a PDF, chunks it, and builds a vector store using Chroma.
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    
    # Chunk the text
    chunks = chunk_text(text)
    
    # Create Document objects
    documents = [
        Document(
            page_content=chunk["text"],
            metadata={
                "chunk_id": f"chunk_{index:04d}",
                "section": chunk["section"],
            },
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create Chroma vector store
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    CHROMA_DIR.mkdir(exist_ok=True)

    vector_store = Chroma.from_documents(
        documents,
        embeddings,
        persist_directory=CHROMA_DIR
    )
    
    print(f"Vector store built and saved to {vector_store}")

def retrieve_top_k(query, k=5):
    """
    Retrieves the top-k most similar documents from the vector store for a given query.
    """
    # Load the vector store
    vector_store = Chroma(
        persist_directory=CHROMA_DIR, 
        embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    )
    
    # Retrieve top-k documents
    results = vector_store.similarity_search(query, k=max(k * 4, 10))

    preferred_sections = infer_preferred_sections(query)
    if preferred_sections:
        preferred_lookup = {section: index for index, section in enumerate(preferred_sections)}
        results.sort(
            key=lambda doc: (
                preferred_lookup.get(doc.metadata.get("section"), len(preferred_lookup)),
            )
        )
    
    return results[:k]

def generate_schema(query, k=3):
    """
    Generates a grounded schema dictionary from retrieved evidence.
    """
    results = retrieve_top_k(query, k=k)

    evidence_snippets = []
    chunk_ids = []
    sections = []

    for doc in results:
        evidence_snippets.append(doc.page_content[:400])
        chunk_ids.append(doc.metadata.get("chunk_id"))
        sections.append(doc.metadata.get("section"))

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
    }


SUMMARY_QUERIES = {
    "problem": "What problem or limitation of prior approaches does BERT solve?",
    "method": "What method or training approach does BERT use?",
    "results": "What datasets, benchmarks, and results are reported for BERT?",
}


GOLD_PATH = Path("outputs/bert_gold.md")


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


def retrieve_summary_evidence(summary_queries, top_k=3):
    """
    Retrieves top chunks for each fixed summary query and returns a structured dict.
    """
    summary_evidence = {}

    for field, query in summary_queries.items():
        retrieved_docs = retrieve_top_k(query, k=top_k)
        summary_evidence[field] = {
            "query": query,
            "retrieved_chunks": [
                {
                    "chunk_id": doc.metadata.get("chunk_id"),
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
        summary[field] = generate_schema(payload["query"], k=len(payload["retrieved_chunks"]))

    return summary


if __name__ == "__main__":
    pdf_path = DATA_DIR / "bert.pdf"

    print("\n--- Smoke Test: PDF Extraction ---")
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

