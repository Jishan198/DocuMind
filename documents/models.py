import uuid
from django.db import models
from django.conf import settings
from pgvector.django import VectorField


class Document(models.Model):
    """Represents an uploaded document belonging to a tenant."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        READY = 'READY', 'Ready'
        FAILED = 'FAILED', 'Failed'

    class FileType(models.TextChoices):
        PDF = 'PDF', 'PDF'
        DOCX = 'DOCX', 'DOCX'
        TXT = 'TXT', 'TXT'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='documents'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    title = models.CharField(max_length=500)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    file_size = models.PositiveIntegerField(help_text='File size in bytes')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    chunk_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'documents_document'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"


class DocumentChunk(models.Model):
    """
    A single chunk of text from a document, with its vector embedding.
    This is the core unit for semantic search.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    content = models.TextField()
    embedding = VectorField(dimensions=3072)  # Gemini text-embedding-004 outputs 768 dims
    chunk_index = models.PositiveIntegerField()  # Position in original document
    page_number = models.PositiveIntegerField(null=True, blank=True)
    token_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents_chunk'
        ordering = ['document', 'chunk_index']
        indexes = [
            # For fast tenant-scoped chunk retrieval
            models.Index(fields=['document', 'chunk_index']),
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"

# Create your models here.
