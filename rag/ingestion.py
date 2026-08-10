import re
import pymupdf

NUMBERED_SECTION_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Z].+)$")
ROMAN_NUMERAL_SECTION_PATTERN = re.compile(r"^[IVXLCDM]{1,6}\.\s+[A-Z].+")

DATE_LIKE_PATTERN = re.compile(r"^\d{1,2}\s+[A-Za-z]+\s+\d{4}$")
NAMED_SECTION_HEADERS = {
    "abstract",
    "introduction",
    "related work",
    "experiments",
    "conclusion",
    "results",
    "discussion",
    "summary",
    "methods",
    "method",
    "star methods",
    "materials and methods",
    "background",
    "limitations",
    "future work",
    "acknowledgments",
    "acknowledgements",
    "key resources table",
    "experimental model and subject details",
    "quantification and statistical analysis",
    "supplemental information",
}
DECORATIVE_HEADER_CHARS = re.compile(r"[^A-Za-z0-9 ]+")

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


def normalize_header_text(text):
    """
    Strips decorative glyphs so headers can be matched against the plain-text whitelist
    regardless of styling.
    """
    normalized = DECORATIVE_HEADER_CHARS.sub(" ", text)
    return re.sub(r"\s+", " ", normalized).strip().lower()


FIGURE_TABLE_LABEL_PATTERN = re.compile(r"^(figure|fig\.?|table)\s*$", re.IGNORECASE)


def is_section_header(line, previous_line=None):
    """
    Heuristic detector for major paper section headers.
    """
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > 80:
        return False

    if previous_line and FIGURE_TABLE_LABEL_PATTERN.match(previous_line.strip()):
        return False

    if stripped[0].isupper() and normalize_header_text(stripped) in NAMED_SECTION_HEADERS:
        return True

    if ROMAN_NUMERAL_SECTION_PATTERN.match(stripped):
        if any(char.isdigit() for char in stripped):
            return False
        if "," in stripped:
            return False
        if len(stripped.split()) > 6:
            return False
        return True

    numbered_match = NUMBERED_SECTION_PATTERN.match(stripped)
    if not numbered_match:
        return False

    if DATE_LIKE_PATTERN.match(stripped):
        return False

    leading_number = int(numbered_match.group(1).split(".")[0])
    if leading_number > 20:
        return False

    title_part = numbered_match.group(2)
    if "," in title_part:
        return False

    if title_part.endswith((".", ",", ";", ":")):
        return False
    if ". " in title_part:
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
    previous_line = None

    for line in lines:
        if not line:
            if current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue

        if is_section_header(line, previous_line=previous_line):
            if current_lines:
                sections.append({
                    "section": current_title,
                    "text": "\n".join(current_lines).strip(),
                })
            current_title = line
            current_lines = []
            previous_line = line
            continue

        current_lines.append(line)
        previous_line = line

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