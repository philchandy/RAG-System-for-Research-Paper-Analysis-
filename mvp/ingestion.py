import re
import pymupdf

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

    if not NUMBERED_SECTION_PATTERN.match(stripped):
        return False

    # Reject sentence fragments that happen to start with a number,
    # such as "0.3 F1 behind fine-tuning the entire model. This".
    if stripped.endswith((".", ",", ";", ":")):
        return False
    if ". " in stripped:
        return False
    if stripped.startswith("0"):
        return False
    if len(stripped.split()) > 8:
        return False

    return True


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

    detected_sections = [section for section in sections if section["section"] != "Front Matter"]
    if not detected_sections:
        normalized = normalize_pdf_text("\n\n".join(section["text"] for section in sections))
        if normalized:
            return [{"section": "Document", "text": normalized}]
        return []

    cleaned_sections = []
    for section in sections:
        normalized = normalize_pdf_text(section["text"])
        if normalized:
            cleaned_sections.append({
                "section": section["section"],
                "text": normalized,
            })

    return cleaned_sections

def extract_page_text(page):
    """
    Extracts page text in column-aware reading order.

    Two-column papers break naive y-sorted extraction, so blocks are
    ordered by column (left of page midline first) and then top-to-bottom.
    Ligatures (fi, fl) are expanded instead of preserved as single glyphs.
    """
    flags = pymupdf.TEXTFLAGS_TEXT & ~pymupdf.TEXT_PRESERVE_LIGATURES
    blocks = page.get_text("blocks", flags=flags)
    midline = page.rect.width / 2

    def block_order(block):
        x0, y0 = block[0], block[1]
        column = 0 if x0 < midline else 1
        return (column, y0, x0)

    text_blocks = [block for block in blocks if block[6] == 0]  # text blocks only
    text_blocks.sort(key=block_order)
    return "\n".join(block[4] for block in text_blocks)


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    """
    text_parts = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            text_parts.append(extract_page_text(page))
    return trim_back_matter("\n".join(text_parts))