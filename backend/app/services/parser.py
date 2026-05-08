from pathlib import Path
from pypdf import PdfReader
from docx import Document
def parse_upload(file_path: str) -> str:
    path = Path(file_path); suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join([(page.extract_text() or "") for page in reader.pages]).strip()
    if suffix == ".docx":
        doc = Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs]).strip()
    if suffix in [".txt", ".md"]:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    raise ValueError("Unsupported file type. Use PDF, DOCX, TXT, or MD.")
