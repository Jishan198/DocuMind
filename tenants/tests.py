import pytest
from django.urls import reverse
from tenants.models import Organization, Membership


@pytest.mark.django_db
class TestTenantIsolation:
    def test_authenticated_user_sees_dashboard(self, auth_client):
        response = auth_client.get(reverse('dashboard'))
        assert response.status_code == 200

    def test_viewer_cannot_access_upload(self, client, viewer_user, viewer_membership):
        client.force_login(viewer_user)
        response = client.get(reverse('upload'))
        assert response.status_code == 302

    def test_org_slug_is_unique(self, db, org):
        from django.utils.text import slugify
        slug = slugify('Test Org')
        assert Organization.objects.filter(slug=slug).count() == 1

    def test_membership_roles(self, db, user, org, owner_membership):
        membership = Membership.objects.get(user=user, organization=org)
        assert membership.role == Membership.Role.OWNER

    def test_owner_can_access_audit_log(self, auth_client):
        response = auth_client.get(reverse('audit_log'))
        assert response.status_code == 200

    def test_viewer_cannot_access_audit_log(self, client, viewer_user, viewer_membership):
        client.force_login(viewer_user)
        response = client.get(reverse('audit_log'))
        assert response.status_code == 302
# Create your tests here.
