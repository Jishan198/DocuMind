from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'organization', 'ip_address', 'created_at')
    list_filter = ('action', 'organization', 'created_at')
    search_fields = ('user__email', 'action', 'organization__name')
    readonly_fields = ('user', 'organization', 'action', 'ip_address', 'payload', 'created_at')
    
    def has_add_permission(self, request):
        # Audit logs should be immutable
        return False

    def has_change_permission(self, request, obj=None):
        return False
