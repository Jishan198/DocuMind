from rest_framework.permissions import BasePermission
from .models import Membership


class IsTenantMember(BasePermission):
    """Allow access only to active members of the current tenant."""

    def has_permission(self, request, view):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id or not request.user.is_authenticated:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            is_active=True
        ).exists()


class IsTenantAdmin(BasePermission):
    """Allow access only to OWNER or ADMIN of the current tenant."""

    def has_permission(self, request, view):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id or not request.user.is_authenticated:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__in=[Membership.Role.OWNER, Membership.Role.ADMIN],
            is_active=True
        ).exists()


class IsTenantOwner(BasePermission):
    """Allow access only to OWNER of the current tenant."""

    def has_permission(self, request, view):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id or not request.user.is_authenticated:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role=Membership.Role.OWNER,
            is_active=True
        ).exists()