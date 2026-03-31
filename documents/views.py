import structlog
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .serializers import DocumentUploadSerializer, DocumentListSerializer, DocumentDetailSerializer
from .tasks import ingest_document
from tenants.permissions import IsTenantMember, IsTenantAdmin

logger = structlog.get_logger(__name__)


class DocumentUploadView(generics.CreateAPIView):
    """Upload a document and trigger async ingestion pipeline."""
    serializer_class = DocumentUploadSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        document = serializer.save(
            organization=self.request.organization,
            uploaded_by=self.request.user
        )
        # Fire Celery task asynchronously
        ingest_document.delay(str(document.id))
        logger.info("document_upload_queued", document_id=str(document.id))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                'message': 'Document uploaded. Processing started.',
                'document': serializer.data
            },
            status=status.HTTP_202_ACCEPTED  # 202 = accepted but not yet processed
        )


class DocumentListView(generics.ListAPIView):
    """List all documents for the current tenant."""
    serializer_class = DocumentListSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Document.objects.filter(
            organization=self.request.organization
        ).select_related('uploaded_by')


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """Get or delete a specific document."""
    serializer_class = DocumentDetailSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Document.objects.filter(organization=self.request.organization)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        # Only admins can delete
        from tenants.models import Membership
        org_id = request.headers.get('X-Organization-ID')
        is_admin = Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__in=[Membership.Role.OWNER, Membership.Role.ADMIN],
            is_active=True
        ).exists()

        if not is_admin:
            return Response(
                {'error': 'Only admins can delete documents.'},
                status=status.HTTP_403_FORBIDDEN
            )

        document.file.delete(save=False)  # Delete physical file too
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Create your views here.
