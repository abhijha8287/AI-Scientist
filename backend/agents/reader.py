import uuid
from pathlib import Path
import fitz  # PyMuPDF


def extract_chunks(pdf_path: str, paper_id: str, chunk_size: int = 1500) -> list[dict]:
    path = Path(pdf_path)
    if path.suffix == ".txt":
        try:
            full_text = path.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Cannot read text file {pdf_path}: {e}")
    else:
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise ValueError(f"Cannot open PDF {pdf_path}: {e}")
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

    if not full_text.strip():
        raise ValueError(f"PDF {pdf_path} contains no extractable text (may be scanned image)")

    words = full_text.split()
    chunks = []
    current_words: list[str] = []
    current_len = 0

    for word in words:
        current_words.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append({
                "id": str(uuid.uuid4()),
                "paper_id": paper_id,
                "text": " ".join(current_words),
                "chunk_index": len(chunks),
            })
            # 10% overlap
            overlap_count = max(1, len(current_words) // 10)
            current_words = current_words[-overlap_count:]
            current_len = sum(len(w) + 1 for w in current_words)

    if current_words:
        chunks.append({
            "id": str(uuid.uuid4()),
            "paper_id": paper_id,
            "text": " ".join(current_words),
            "chunk_index": len(chunks),
        })

    return chunks
