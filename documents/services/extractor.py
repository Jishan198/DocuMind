import io
from typing import Optional
import PyPDF2
import docx


class TextExtractor:
    """
    Extracts raw text from uploaded files.
    Returns a list of (page_number, text) tuples for page-aware chunking.
    """

    def extract(self, file_path: str, file_type: str) -> list[tuple[int, str]]:
        file_type = file_type.upper()
        if file_type == 'PDF':
            return self._extract_pdf(file_path)
        elif file_type == 'DOCX':
            return self._extract_docx(file_path)
        elif file_type == 'TXT':
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf(self, file_path: str) -> list[tuple[int, str]]:
        pages = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ''
                if text.strip():
                    pages.append((i, text))
        return pages

    def _extract_docx(self, file_path: str) -> list[tuple[int, str]]:
        doc = docx.Document(file_path)
        full_text = '\n'.join(
            para.text for para in doc.paragraphs if para.text.strip()
        )
        return [(1, full_text)]  # DOCX has no page concept, treat as single page

    def _extract_txt(self, file_path: str) -> list[tuple[int, str]]:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return [(1, f.read())]