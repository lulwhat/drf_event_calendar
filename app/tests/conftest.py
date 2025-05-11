import pytest
from celery import current_app
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def organizer():
    return User.objects.create_user(
        username='organizer',
        email='organizer@example.com',
        password='testpass123'
    )


@pytest.fixture(autouse=True)
def celery_eager():
    current_app.conf.task_always_eager = True
    yield
    current_app.conf.task_always_eager = False
