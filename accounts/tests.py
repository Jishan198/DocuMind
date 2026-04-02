import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegistration:
    def test_register_creates_user_and_org(self, client):
        response = client.post(reverse('register_view'), {
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'StrongPass123!',
            'org_name': 'New Org'
        })
        assert response.status_code == 302
        assert User.objects.filter(email='new@example.com').exists()

    def test_register_duplicate_email_fails(self, client, user):
        response = client.post(reverse('register_view'), {
            'email': 'test@example.com',
            'username': 'another',
            'password': 'StrongPass123!',
            'org_name': 'Another Org'
        })
        assert b'already registered' in response.content

    def test_register_creates_owner_membership(self, client):
        from tenants.models import Membership
        client.post(reverse('register_view'), {
            'email': 'owner@example.com',
            'username': 'owneruser',
            'password': 'StrongPass123!',
            'org_name': 'Owner Org'
        })
        user = User.objects.get(email='owner@example.com')
        membership = Membership.objects.get(user=user)
        assert membership.role == Membership.Role.OWNER


@pytest.mark.django_db
class TestLogin:
    def test_login_valid_credentials(self, client, user, owner_membership):
        response = client.post(reverse('login_view'), {
            'email': 'test@example.com',
            'password': 'StrongPass123!'
        }, follow=True)
        assert response.status_code == 200
        assert response.redirect_chain

    def test_login_wrong_password(self, client, user):
        response = client.post(reverse('login_view'), {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        assert b'Invalid credentials' in response.content

    def test_login_nonexistent_email(self, client):
        response = client.post(reverse('login_view'), {
            'email': 'nobody@example.com',
            'password': 'StrongPass123!'
        })
        assert b'No account' in response.content

    def test_unauthenticated_redirects_to_login(self, client):
        response = client.get(reverse('dashboard'))
        assert response.status_code == 302
        assert '/auth/login/' in response['Location']
# Create your tests here.
