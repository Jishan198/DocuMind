from rest_framework.permissions import BasePermission
from .models import Membership


class IsTenantMember(BasePermission):
    """
    Allow access to ANY active member of the tenant (including VIEWER).
    Use this for read-only endpoints — listing docs, viewing query history.
    """

    def has_permission(self, request, view):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id or not request.user.is_authenticated:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            is_active=True
        ).exists()


class IsTenantContributor(BasePermission):
    """
    Allow access to OWNER, ADMIN, MEMBER — but NOT VIEWER.
    Use this for write endpoints — uploading documents, running queries.
    VIEWER role is read-only and cannot create or modify content.
    """

    def has_permission(self, request, view):
        org_id = request.headers.get('X-Organization-ID')
        if not org_id or not request.user.is_authenticated:
            return False
        return Membership.objects.filter(
            user=request.user,
            organization_id=org_id,
            role__in=[
                Membership.Role.OWNER,
                Membership.Role.ADMIN,
                Membership.Role.MEMBER,
            ],
            is_active=True
        ).exists()


class IsTenantAdmin(BasePermission):
    """
    Allow access only to OWNER or ADMIN.
    Use this for management endpoints — deleting docs, viewing audit logs,
    inviting members.
    """

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
    """
    Allow access only to OWNER.
    Use this for org-level settings and billing.
    """

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