import re
from PyPDF2 import PdfReader

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

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyPDF2.
    """
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return trim_back_matter(text)