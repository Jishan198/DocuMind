import pytest
from django.contrib.auth import get_user_model
from tenants.models import Organization, Membership

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('CREATE EXTENSION IF NOT EXISTS vector;')
            cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        username='testuser',
        password='StrongPass123!'
    )


@pytest.fixture
def org(db):
    return Organization.objects.create(
        name='Test Org',
        slug='test-org'
    )


@pytest.fixture
def owner_membership(db, user, org):
    return Membership.objects.create(
        user=user,
        organization=org,
        role=Membership.Role.OWNER
    )


@pytest.fixture
def viewer_user(db):
    return User.objects.create_user(
        email='viewer@example.com',
        username='vieweruser',
        password='StrongPass123!'
    )


@pytest.fixture
def viewer_membership(db, viewer_user, org):
    return Membership.objects.create(
        user=viewer_user,
        organization=org,
        role=Membership.Role.VIEWER
    )


@pytest.fixture
def auth_client(client, user, owner_membership):
    client.force_login(user)
    return client