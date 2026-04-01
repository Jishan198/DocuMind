import structlog
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Document
from .serializers import DocumentUploadSerializer, DocumentListSerializer, DocumentDetailSerializer
from .tasks import ingest_document
from tenants.permissions import IsTenantMember, IsTenantContributor, IsTenantAdmin

logger = structlog.get_logger(__name__)


class DocumentUploadView(generics.CreateAPIView):
    """
    Upload a document and trigger async ingestion pipeline.
    Requires MEMBER role or above — VIEWER cannot upload.
    """
    serializer_class = DocumentUploadSerializer
    permission_classes = [IsAuthenticated, IsTenantContributor]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        document = serializer.save(
            organization=self.request.organization,
            uploaded_by=self.request.user
        )
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
            status=status.HTTP_202_ACCEPTED
        )


class DocumentListView(generics.ListAPIView):
    """
    List all documents for the current tenant.
    All roles including VIEWER can see the document list.
    """
    serializer_class = DocumentListSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Document.objects.filter(
            organization=self.request.organization
        ).select_related('uploaded_by')


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    """
    Get or delete a specific document.
    - GET: any member including VIEWER
    - DELETE: ADMIN or OWNER only
    """
    serializer_class = DocumentDetailSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Document.objects.filter(organization=self.request.organization)

    def destroy(self, request, *args, **kwargs):
        # Enforce admin-only delete using the permission class directly
        admin_permission = IsTenantAdmin()
        if not admin_permission.has_permission(request, self):
            return Response(
                {'error': 'Only admins can delete documents.'},
                status=status.HTTP_403_FORBIDDEN
            )

        document = self.get_object()
        document.file.delete(save=False)
        document.delete()
        logger.info("document_deleted",
                    document_id=str(document.id),
                    deleted_by=str(request.user.id))
        return Response(status=status.HTTP_204_NO_CONTENT)

# Create your views here.
