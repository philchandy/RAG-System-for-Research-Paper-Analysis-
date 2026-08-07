import re
from rag.ingestion import split_into_sections


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