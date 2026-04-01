import structlog
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

logger = structlog.get_logger(__name__)


def health_check(request):
    """
    Public health check endpoint.
    Returns the status of every critical service dependency.
    Used by Docker, load balancers, and uptime monitors.

    Response codes:
        200 — all systems healthy
        503 — one or more systems degraded
    """
    health = {
        'status': 'healthy',
        'services': {}
    }
    all_healthy = True

    # ── 1. PostgreSQL ─────────────────────────────────────────────────────
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health['services']['database'] = {'status': 'healthy'}
    except Exception as e:
        health['services']['database'] = {'status': 'unhealthy', 'error': str(e)}
        all_healthy = False
        logger.error("health_check_db_failed", error=str(e))

    # ── 2. Redis ──────────────────────────────────────────────────────────
    try:
        cache.set('health_check_ping', 'pong', timeout=10)
        result = cache.get('health_check_ping')
        if result == 'pong':
            health['services']['redis'] = {'status': 'healthy'}
        else:
            raise ValueError("Cache read returned unexpected value")
    except Exception as e:
        health['services']['redis'] = {'status': 'unhealthy', 'error': str(e)}
        all_healthy = False
        logger.error("health_check_redis_failed", error=str(e))

    # ── 3. Celery workers ─────────────────────────────────────────────────
    try:
        from config.celery import app as celery_app
        inspector = celery_app.control.inspect(timeout=2.0)
        active = inspector.active()
        if active:
            worker_count = len(active)
            health['services']['celery'] = {
                'status': 'healthy',
                'workers': worker_count
            }
        else:
            health['services']['celery'] = {
                'status': 'unhealthy',
                'error': 'No active workers found'
            }
            all_healthy = False
    except Exception as e:
        health['services']['celery'] = {'status': 'unhealthy', 'error': str(e)}
        all_healthy = False
        logger.error("health_check_celery_failed", error=str(e))

    # ── Final status ──────────────────────────────────────────────────────
    if not all_healthy:
        health['status'] = 'degraded'

    http_status = 200 if all_healthy else 503
    return JsonResponse(health, status=http_status)