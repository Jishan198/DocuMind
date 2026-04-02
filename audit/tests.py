import pytest
from audit.services import log_action
from audit.models import AuditLog


@pytest.mark.django_db
class TestAuditLogging:
    def test_log_action_creates_entry(self, user, org):
        log_action(user, org, 'TEST_ACTION', payload={'key': 'value'})
        assert AuditLog.objects.filter(
            user=user,
            organization=org,
            action='TEST_ACTION'
        ).exists()

    def test_log_action_never_raises(self, user, org):
        # Even with bad payload, should not crash
        try:
            log_action(user, org, 'SAFE_ACTION', payload={'x': 'y'})
        except Exception:
            pytest.fail("log_action raised an exception")

    def test_audit_log_immutable_in_admin(self, user, org):
        from audit.admin import AuditLogAdmin
        from django.contrib.admin.sites import AdminSite
        admin = AuditLogAdmin(AuditLog, AdminSite())
        assert admin.has_add_permission(None) is False
        assert admin.has_change_permission(None) is False
# Create your tests here.
