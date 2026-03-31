import structlog
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = structlog.get_logger(__name__)


def broadcast_progress(org_id, document_id, title, status, stage, progress, message, chunk_count=0):
    """Send a real-time progress update via Django Channels."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'document_progress_{org_id}',
        {
            'type': 'document.progress',
            'document_id': str(document_id),
            'title': title,
            'status': status,
            'stage': stage,
            'progress': progress,
            'message': message,
            'chunk_count': chunk_count,
        }
    )


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    acks_late=True           # Only mark done after successful completion
)
def ingest_document(self, document_id: str):
    """
    Full document ingestion pipeline:
    1. Extract text from file
    2. Chunk the text
    3. Generate embeddings
    4. Store chunks + vectors in DB
    5. Update document status

    Broadcasts real-time progress via WebSocket at each stage.
    """
    from .models import Document, DocumentChunk
    from .services.extractor import TextExtractor
    from .services.chunker import DocumentChunker
    from .services.embedder import EmbeddingService

    log = logger.bind(document_id=document_id, task_id=self.request.id)

    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        log.error("document_not_found")
        return

    org_id = str(document.organization_id)
    title = document.title

    try:
        # Mark as processing
        document.status = Document.Status.PROCESSING
        document.save(update_fields=['status', 'updated_at'])
        log.info("ingestion_started")

        broadcast_progress(org_id, document_id, title,
                          'PROCESSING', 'extracting', 10,
                          'Extracting text from document...')

        # Step 1: Extract text
        extractor = TextExtractor()
        pages = extractor.extract(document.file.path, document.file_type)
        log.info("text_extracted", page_count=len(pages))

        broadcast_progress(org_id, document_id, title,
                          'PROCESSING', 'chunking', 30,
                          f'Text extracted — {len(pages)} pages. Chunking...')

        # Step 2: Chunk text
        chunker = DocumentChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk_pages(pages)
        log.info("text_chunked", chunk_count=len(chunks))

        if not chunks:
            raise ValueError("No text could be extracted from the document.")

        broadcast_progress(org_id, document_id, title,
                          'PROCESSING', 'embedding', 50,
                          f'{len(chunks)} chunks created. Generating embeddings...')

        # Step 3: Generate embeddings
        embedder = EmbeddingService()
        texts = [chunk.content for chunk in chunks]
        embeddings = embedder.embed_texts(texts)
        log.info("embeddings_generated", count=len(embeddings))

        broadcast_progress(org_id, document_id, title,
                          'PROCESSING', 'saving', 80,
                          'Embeddings generated. Saving to database...')

        # Step 4: Bulk save chunks + embeddings
        # Delete existing chunks first (handles re-ingestion)
        DocumentChunk.objects.filter(document=document).delete()

        chunk_objects = [
            DocumentChunk(
                document=document,
                content=chunks[i].content,
                embedding=embeddings[i],
                chunk_index=chunks[i].chunk_index,
                page_number=chunks[i].page_number,
                token_count=chunks[i].token_count,
            )
            for i in range(len(chunks))
        ]
        DocumentChunk.objects.bulk_create(chunk_objects, batch_size=100)

        # Step 5: Mark as ready
        document.status = Document.Status.READY
        document.chunk_count = len(chunks)
        document.error_message = ''
        document.save(update_fields=['status', 'chunk_count', 'error_message', 'updated_at'])
        log.info("ingestion_complete", chunk_count=len(chunks))

        broadcast_progress(org_id, document_id, title,
                          'READY', 'complete', 100,
                          f'Ready! {len(chunks)} chunks indexed.',
                          chunk_count=len(chunks))

    except Exception as exc:
        log.error("ingestion_failed", error=str(exc))
        document.status = Document.Status.FAILED
        document.error_message = str(exc)
        document.save(update_fields=['status', 'error_message', 'updated_at'])

        broadcast_progress(org_id, document_id, title,
                          'FAILED', 'failed', 0,
                          f'Failed: {str(exc)[:100]}')

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))