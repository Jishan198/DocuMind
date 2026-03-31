from django.utils.functional import SimpleLazyObject
from .models import Organization


def get_organization(request):
    org_id = request.headers.get('X-Organization-ID')
    if not org_id:
        return None
    try:
        return Organization.objects.get(id=org_id, is_active=True)
    except (Organization.DoesNotExist, ValueError):
        return None


class TenantMiddleware:
    """
    Attaches the current Organization to every request as request.organization.
    Views can use this to scope querysets to the tenant automatically.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organization = SimpleLazyObject(lambda: get_organization(request))
        return self.get_response(request)