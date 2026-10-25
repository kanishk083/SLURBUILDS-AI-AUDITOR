from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
from pypdf import PdfReader
from backend.config import settings


class DocumentError(ValueError):
    pass


@dataclass
class Passage:
    text: str
    page: int | None
    line_start: int
    line_end: int
    context: str


def parse(content: bytes, extension: str, name: str) -> list[Passage]:
    cfg = settings()
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise DocumentError("This file is not a valid PDF.")
        try:
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise DocumentError("Password-protected PDFs are not supported.")
            if len(reader.pages) > cfg.max_document_pages:
                raise DocumentError(f"PDF exceeds {cfg.max_document_pages} pages.")
            pages = [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
        except DocumentError:
            raise
        except Exception as exc:
            raise DocumentError("PDF could not be parsed. Upload a valid, text-readable PDF.") from exc
    else:
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentError("TXT and Markdown files must use UTF-8 encoding.") from exc
        if "\x00" in decoded:
            raise DocumentError("Binary content is not accepted as text.")
        pages = [(None, decoded)]
    if sum(len(text) for _, text in pages) > cfg.max_document_chars:
        raise DocumentError(f"Extracted text exceeds {cfg.max_document_chars:,} characters.")
    if not any(text.strip() for _, text in pages):
        raise DocumentError("needs_ocr: no readable text found; upload OCR text or a digital-text PDF.")
    output = []
    for page, text in pages:
        heading = Path(name).stem
        buffer, start, count = [], 1, 0
        for line_no, line in enumerate(text.splitlines(), 1):
            if line.startswith("#"):
                if buffer:
                    output.append(Passage("\n".join(buffer).strip(), page, start, line_no - 1, heading))
                    buffer = []
                    count = 0
                heading = re.sub(r"^#+\s*", "", line)[:160]
            if not line.strip():
                if buffer:
                    output.append(Passage("\n".join(buffer).strip(), page, start, line_no - 1, heading))
                    buffer, count = [], 0
                continue
            if buffer and count + len(line) > 650:
                output.append(Passage("\n".join(buffer).strip(), page, start, line_no - 1, heading))
                buffer, count = [], 0
            # Bound long single lines so verification never silently truncates an enormous passage.
            if len(line) > 650:
                if buffer:
                    output.append(Passage("\n".join(buffer).strip(), page, start, line_no - 1, heading))
                    buffer, count = [], 0
                words = line.split()
                window = []
                for word in words:
                    if sum(map(len, window)) + len(window) + len(word) > 650 and window:
                        output.append(Passage(" ".join(window), page, line_no, line_no, heading))
                        window = []
                    window.append(word)
                if window:
                    output.append(Passage(" ".join(window), page, line_no, line_no, heading))
                continue
            if not buffer:
                start = line_no
            buffer.append(line)
            count += len(line) + 1
        if buffer:
            output.append(Passage("\n".join(buffer).strip(), page, start, len(text.splitlines()), heading))
    return [p for p in output if p.text]


def extract_claims(answer: str, limit: int = 20) -> list[dict]:
    spans = []
    pattern = r"[^\n;.!?]+(?:[.!?](?!\s|$)[^\n;.!?]+)*[.!?]?"
    for match in re.finditer(pattern, answer):
        raw = match.group()
        stripped = re.sub(r"^\s*(?:[-*•]|\d+[.)])?\s*", "", raw).strip()
        if not stripped:
            continue
        start = match.start() + raw.find(stripped)
        spans.append(
            {
                "id": f"C{len(spans) + 1}",
                "text": stripped,
                "answer_span": {"start": start, "end": start + len(stripped)},
            }
        )
    if not spans:
        raise DocumentError("No factual statements were found in the answer.")
    if len(spans) > limit:
        raise DocumentError(
            f"Answer contains more than {limit} candidate claims. Split it into smaller audits."
        )
    return spans
