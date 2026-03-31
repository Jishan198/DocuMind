import structlog
from .models import AuditLog

logger = structlog.get_logger(__name__)

def log_action(user, organization, action, request=None, payload=None):
    """
    Helper function to log significant system actions safely.
    Handles extraction of IP address from the request if provided.
    Always use keyword arguments for explicit parameters.
    """
    if payload is None:
        payload = {}

    ip_address = None
    if request:
        # Standard way to get client IP in Django, factoring in typical proxy headers
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    try:
        log_entry = AuditLog.objects.create(
            user=user,
            organization=organization,
            action=action,
            ip_address=ip_address,
            payload=payload
        )
        logger.info(
            "audit_action", 
            action=action, 
            user_id=str(user.id) if user else None, 
            org_id=str(organization.id) if organization else None
        )
        return log_entry
    except Exception as e:
        # We don't want audit logging failures to break the main application flow
        logger.error(
            "audit_log_creation_failed", 
            action=action, 
            error=str(e),
            user_id=str(user.id) if user else None, 
            org_id=str(organization.id) if organization else None
        )
        return None
