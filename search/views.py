import time
import structlog
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from tenants.permissions import IsTenantMember
from .models import QueryLog
from .serializers import QueryRequestSerializer, QueryResponseSerializer, QueryLogSerializer
from .services.retriever import HybridRetriever
from .services.generator import AnswerGenerator

logger = structlog.get_logger(__name__)


from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from audit.services import log_action
from documents.utils import sanitize_text

@method_decorator(ratelimit(key='ip', rate='30/m', block=False), name='post')
class QueryView(generics.GenericAPIView):
    """
    Core RAG endpoint. Takes a question, retrieves relevant chunks,
    generates an answer with citations.
    """
    serializer_class = QueryRequestSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def post(self, request, *args, **kwargs):
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Rate limit exceeded. Please wait before asking more questions.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Sanitize query to prevent any stored XSS or injection weirdness
        question = sanitize_text(serializer.validated_data['question'])

        start_time = time.time()

        try:
            # Step 1: Retrieve relevant chunks
            retriever = HybridRetriever(
                organization=request.organization,
                top_k=5
            )
            chunks = retriever.retrieve(question)

            # Step 2: Generate answer
            generator = AnswerGenerator()
            result = generator.generate(question, chunks)

            response_time_ms = int((time.time() - start_time) * 1000)

            # Step 3: Log the query
            QueryLog.objects.create(
                organization=request.organization,
                user=request.user,
                question=question,
                answer=result['answer'],
                sources=result['sources'],
                tokens_used=result['tokens_used'],
                response_time_ms=response_time_ms
            )
            
            # Step 4: Audit trail
            log_action(
                request.user,
                request.organization,
                'QUERY_EXECUTED',
                request,
                payload={'question': question, 'tokens_used': result['tokens_used']}
            )

            return Response({
                'question': question,
                'answer': result['answer'],
                'sources': result['sources'],
                'tokens_used': result['tokens_used'],
                'response_time_ms': response_time_ms
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("query_failed", error=str(e))
            return Response(
                {'error': 'Failed to process query.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QueryHistoryView(generics.ListAPIView):
    """Returns paginated query history for the current tenant."""
    serializer_class = QueryLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return QueryLog.objects.filter(
            organization=self.request.organization
        ).select_related('user')

# Create your views here.
