import uuid
from django.db import models
from django.conf import settings


class QueryLog(models.Model):
    """Logs every query made by a user for analytics and audit purposes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        'tenants.Organization',
        on_delete=models.CASCADE,
        related_name='queries'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='queries'
    )
    question = models.TextField()
    answer = models.TextField()
    sources = models.JSONField(default=list)  # List of cited chunk references
    tokens_used = models.PositiveIntegerField(default=0)
    response_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_querylog'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} asked: {self.question[:50]}"
        
# Create your models here.
