from dataclasses import dataclass
from typing import Optional


@dataclass
class TextChunk:
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    token_count: int = 0


class DocumentChunker:
    """
    Splits document text into overlapping chunks for embedding.

    Why overlap? Without it, answers that span chunk boundaries get missed.
    500 tokens per chunk with 50 token overlap is a solid default for RAG.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, page_number: Optional[int] = None) -> list[TextChunk]:
        """Split text into overlapping word-based chunks."""
        words = text.split()
        chunks = []
        index = 0
        start = 0

        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            content = ' '.join(chunk_words)

            if content.strip():
                chunks.append(TextChunk(
                    content=content,
                    chunk_index=index,
                    page_number=page_number,
                    token_count=len(chunk_words)
                ))
                index += 1

            start += self.chunk_size - self.overlap  # Overlap by stepping back

        return chunks

    def chunk_pages(self, pages: list[tuple[int, str]]) -> list[TextChunk]:
        """
        Chunk a list of (page_number, text) tuples.
        Preserves page number per chunk for citation purposes.
        """
        all_chunks = []
        global_index = 0

        for page_number, text in pages:
            page_chunks = self.chunk_text(text, page_number)
            for chunk in page_chunks:
                chunk.chunk_index = global_index
                global_index += 1
            all_chunks.extend(page_chunks)

        return all_chunks