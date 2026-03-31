from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from tenants.permissions import IsTenantAdmin
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(generics.ListAPIView):
    """
    Paginated audit log for the current tenant.
    Admin-only — shows who did what and when.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_queryset(self):
        return AuditLog.objects.filter(
            organization=self.request.organization
        ).select_related('user').order_by('-created_at')

# Create your views here.
