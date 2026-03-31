import time
import structlog
from google import genai
from django.conf import settings

logger = structlog.get_logger(__name__)


class AnswerGenerator:
    """
    Generates answers using Gemini with retrieved context chunks.
    Uses RAG pattern: Retrieval Augmented Generation.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model = "models/gemini-2.0-flash-lite"

    def generate(self, question: str, chunks: list[dict]) -> dict:
        """
        Generate an answer with citations from retrieved chunks.
        Returns answer text + source references.
        """
        if not chunks:
            return {
                'answer': 'No relevant documents found to answer your question.',
                'sources': [],
                'tokens_used': 0
            }

        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}] Document: '{chunk['document_title']}', "
                f"Page {chunk['page_number']}\n{chunk['content']}"
            )
        context = "\n\n".join(context_parts)

        prompt = f"""You are a helpful assistant answering questions based on the provided documents.

Context from documents:
{context}

Question: {question}

Instructions:
- Answer based only on the provided context
- Cite sources using [Source N] notation
- If the context doesn't contain enough information, say so clearly
- Be concise and accurate

Answer:"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            answer = response.text

            # Build source references
            sources = [
                {
                    'document_title': chunk['document_title'],
                    'document_id': str(chunk['document_id']),
                    'page_number': chunk['page_number'],
                    'chunk_index': chunk['chunk_index'],
                    'score': round(float(chunk['combined_score']), 4)
                }
                for chunk in chunks
            ]

            tokens_used = 0
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens_used = getattr(response.usage_metadata, 'total_token_count', 0)

            logger.info("answer_generated",
                       question=question[:50],
                       tokens_used=tokens_used)

            return {
                'answer': answer,
                'sources': sources,
                'tokens_used': tokens_used
            }

        except Exception as e:
            logger.error("generation_failed", error=str(e))
            raise