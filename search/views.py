import time
import hashlib
import structlog
from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from tenants.permissions import IsTenantMember, IsTenantContributor
from .models import QueryLog
from .serializers import QueryRequestSerializer, QueryResponseSerializer, QueryLogSerializer
from .services.retriever import HybridRetriever
from .services.generator import AnswerGenerator

logger = structlog.get_logger(__name__)

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from audit.services import log_action
from documents.utils import sanitize_text

# Cache query results for 5 minutes — identical questions from same org
# get an instant answer without hitting the AI API again.
QUERY_CACHE_TTL = 60 * 5


def _build_cache_key(org_id: str, question: str) -> str:
    """
    Build a deterministic cache key from org + question.
    MD5 keeps the key short and safe for Redis.
    """
    fingerprint = hashlib.md5(f"{org_id}:{question.lower().strip()}".encode()).hexdigest()
    return f"query_result:{fingerprint}"


@method_decorator(ratelimit(key='ip', rate='30/m', block=False), name='post')
class QueryView(generics.GenericAPIView):
    """
    Core RAG endpoint. Takes a question, retrieves relevant chunks,
    generates an answer with citations.

    Caches results in Redis — repeated identical questions return instantly
    with cache_hit: true in the response.

    Requires MEMBER role or above — VIEWER cannot run queries.
    """
    serializer_class = QueryRequestSerializer
    permission_classes = [IsAuthenticated, IsTenantContributor]

    def post(self, request, *args, **kwargs):
        if getattr(request, 'limited', False):
            return Response(
                {'error': 'Rate limit exceeded. Please wait before asking more questions.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = sanitize_text(serializer.validated_data['question'])
        org_id = str(request.organization.id)

        # ── Cache check ──────────────────────────────────────────────────
        cache_key = _build_cache_key(org_id, question)
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info("query_cache_hit", question=question[:50], org_id=org_id)
            return Response({
                'question': question,
                'answer': cached_result['answer'],
                'sources': cached_result['sources'],
                'tokens_used': cached_result['tokens_used'],
                'response_time_ms': cached_result['response_time_ms'],
                'cache_hit': True,
            }, status=status.HTTP_200_OK)

        # ── Cache miss — run the full RAG pipeline ────────────────────────
        start_time = time.time()

        try:
            retriever = HybridRetriever(organization=request.organization, top_k=5)
            chunks = retriever.retrieve(question)

            generator = AnswerGenerator()
            result = generator.generate(question, chunks)

            response_time_ms = int((time.time() - start_time) * 1000)

            # Store in QueryLog for audit + dashboard analytics
            QueryLog.objects.create(
                organization=request.organization,
                user=request.user,
                question=question,
                answer=result['answer'],
                sources=result['sources'],
                tokens_used=result['tokens_used'],
                response_time_ms=response_time_ms
            )

            log_action(
                request.user,
                request.organization,
                'QUERY_EXECUTED',
                request,
                payload={'question': question, 'tokens_used': result['tokens_used']}
            )

            # ── Write to cache ────────────────────────────────────────────
            cache_payload = {
                'answer': result['answer'],
                'sources': result['sources'],
                'tokens_used': result['tokens_used'],
                'response_time_ms': response_time_ms,
            }
            cache.set(cache_key, cache_payload, timeout=QUERY_CACHE_TTL)
            logger.info("query_cache_set", question=question[:50], ttl=QUERY_CACHE_TTL)

            return Response({
                'question': question,
                'answer': result['answer'],
                'sources': result['sources'],
                'tokens_used': result['tokens_used'],
                'response_time_ms': response_time_ms,
                'cache_hit': False,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("query_failed", error=str(e))
            return Response(
                {'error': 'Failed to process query.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QueryHistoryView(generics.ListAPIView):
    """
    Returns paginated query history for the current tenant.
    All members including VIEWER can see query history.
    """
    serializer_class = QueryLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return QueryLog.objects.filter(
            organization=self.request.organization
        ).select_related('user')
# Create your views here.
