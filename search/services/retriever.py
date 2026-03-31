import structlog
from django.db import connection
from documents.models import DocumentChunk
from documents.services.embedder import EmbeddingService

logger = structlog.get_logger(__name__)


class HybridRetriever:
    """
    Retrieves relevant chunks using hybrid search:
    1. Vector similarity search (semantic meaning)
    2. Full-text trigram search (keyword matching)
    Combined for better recall than either alone.
    """

    def __init__(self, organization, top_k: int = 5):
        self.organization = organization
        self.top_k = top_k
        self.embedder = EmbeddingService()

    def retrieve(self, query: str) -> list[dict]:
        """
        Returns top-K most relevant chunks for the query.
        Each result includes content, page number, document title, and score.
        """
        query_embedding = self.embedder.embed_query(query)
        embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'

        # Hybrid query: vector similarity + trigram text search
        sql = """
            SELECT
                dc.id,
                dc.content,
                dc.page_number,
                dc.chunk_index,
                d.title as document_title,
                d.id as document_id,
                1 - (dc.embedding <=> %s::vector) as vector_score,
                similarity(dc.content, %s) as text_score,
                (
                    0.7 * (1 - (dc.embedding <=> %s::vector)) +
                    0.3 * similarity(dc.content, %s)
                ) as combined_score
            FROM documents_chunk dc
            JOIN documents_document d ON dc.document_id = d.id
            WHERE d.organization_id = %s
            AND d.status = 'READY'
            ORDER BY combined_score DESC
            LIMIT %s
        """

        with connection.cursor() as cursor:
            cursor.execute(sql, [
                embedding_str,
                query,
                embedding_str,
                query,
                str(self.organization.id),
                self.top_k
            ])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        results = []
        for row in rows:
            result = dict(zip(columns, row))
            results.append(result)

        logger.info("retrieval_complete",
                   query=query[:50],
                   chunk_count=len(results))
        return results