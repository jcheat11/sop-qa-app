"""Text extraction for SOP documents. One function per format, plus a
dispatcher that picks by file extension. Every function returns plain text.

Kept isolated from app.py and qa.py because this is the module most likely
to be swapped or extended later (e.g. new formats, OCR fallback).
"""

from __future__ import annotations

import io
import os

SCANNED_PDF_ERROR = (
    "This PDF appears to be scanned or image-only. "
    "Text extraction isn't supported for it yet."
)


def extract_docx(file: io.BytesIO | str) -> str:
    """Extract text from a .docx file, preserving heading hierarchy and
    numbered lists, marking inline images, and pipe-separating table rows.

    `file` may be a path or a file-like object (e.g. an uploaded file).
    """
    import docx

    document = docx.Document(file)
    lines: list[str] = []

    body = document.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            para = next(
                (p for p in document.paragraphs if p._p is child), None
            )
            if para is None:
                continue
            lines.append(_render_paragraph(para))
        elif tag == "tbl":
            table = next(
                (t for t in document.tables if t._tbl is child), None
            )
            if table is None:
                continue
            lines.append(_render_table(table))

    return "\n".join(line for line in lines if line is not None).strip() + "\n"


def _render_paragraph(para) -> str | None:
    text = para.text.strip()
    has_image = _paragraph_has_image(para)

    style = (para.style.name or "") if para.style else ""
    if style.startswith("Heading"):
        digits = "".join(ch for ch in style if ch.isdigit())
        level = int(digits) if digits else 1
        prefix = "#" * max(1, level)
        rendered = f"{prefix} {text}" if text else None
    elif not text and not has_image:
        rendered = None
    else:
        rendered = text if text else None

    if has_image:
        rendered = f"{rendered}\n[image omitted]" if rendered else "[image omitted]"

    return rendered


def _paragraph_has_image(para) -> bool:
    xml = para._p.xml
    return "graphicData" in xml or "pic:pic" in xml or "<a:blip" in xml


def _render_table(table) -> str:
    rows = []
    for row in table.rows:
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def extract_pdf(file: io.BytesIO | str) -> str:
    """Extract text from a .pdf file. Raises ValueError with
    SCANNED_PDF_ERROR if the extracted text is empty or near-empty."""
    from pypdf import PdfReader

    reader = PdfReader(file)
    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(pages_text).strip()

    if len(text) < 50:
        raise ValueError(SCANNED_PDF_ERROR)

    return text, len(reader.pages)


def extract_txt(file) -> str:
    """Extract text from a .txt or .md file. `file` may be a path, a
    file-like object, or raw bytes."""
    if isinstance(file, (bytes, bytearray)):
        return file.decode("utf-8", errors="replace")
    if hasattr(file, "read"):
        data = file.read()
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        return data
    with open(file, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract(file, filename: str):
    """Dispatch to the right extractor based on filename extension.

    Returns plain text for .docx/.txt/.md, or (text, page_count) for .pdf.
    Raises ValueError for unsupported extensions or scanned PDFs.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".docx":
        return extract_docx(file)
    if ext == ".pdf":
        return extract_pdf(file)
    if ext in (".txt", ".md"):
        return extract_txt(file)

    raise ValueError(f"Unsupported file extension: {ext}")
