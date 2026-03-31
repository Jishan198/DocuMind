from django.contrib import admin
from .models import QueryLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'tokens_used', 'response_time_ms', 'created_at']
    search_fields = ['question', 'answer']
    readonly_fields = ['answer', 'sources', 'tokens_used', 'response_time_ms']

# Register your models here.
