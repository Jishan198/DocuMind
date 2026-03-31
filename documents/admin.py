from django.contrib import admin
from .models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'file_type', 'status', 'chunk_count', 'created_at']
    list_filter = ['status', 'file_type']
    search_fields = ['title']
    readonly_fields = ['chunk_count', 'error_message', 'created_at', 'updated_at']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'page_number', 'token_count']
    search_fields = ['document__title']
# Register your models here.
