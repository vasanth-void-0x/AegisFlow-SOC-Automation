"""Safe text chunking for RAG ingestion - splits by markdown section headers
first, falling back to fixed-size chunks with overlap for long sections."""
import re


def chunk_markdown(text: str, max_chunk_chars: int = 1200, overlap_chars: int = 150) -> list[dict]:
    """
    Split markdown into chunks aligned to `## ` section headers where possible.
    Returns a list of {"heading": str, "text": str} dicts.
    """
    # Strip YAML frontmatter if present
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)

    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    chunks: list[dict] = []

    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading_match = re.match(r"^##\s+(.+)$", section, re.MULTILINE)
        heading = heading_match.group(1).strip() if heading_match else "Introduction"

        if len(section) <= max_chunk_chars:
            chunks.append({"heading": heading, "text": section})
        else:
            # Fixed-size sub-chunking with overlap for long sections
            start = 0
            while start < len(section):
                end = min(start + max_chunk_chars, len(section))
                chunks.append({"heading": heading, "text": section[start:end]})
                start = end - overlap_chars if end < len(section) else end

    return chunks
