from django.db import models
from django.conf import settings
from tenants.models import Organization

class AuditLog(models.Model):
    """
    Centralized model for tracking all significant actions within an organization.
    Supports compliance and security auditing.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text="The user who performed the action"
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,  
        blank=True, 
        help_text="The organization context for this action"
    )
    
    # Action categorization
    action = models.CharField(max_length=255, db_index=True, help_text="Identifier for the type of action (e.g., DOCUMENT_UPLOADED)")
    
    # Contextual data
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the user")
    payload = models.JSONField(default=dict, blank=True, help_text="Additional metadata related to the action (e.g., document ID, search terms)")
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} on {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
