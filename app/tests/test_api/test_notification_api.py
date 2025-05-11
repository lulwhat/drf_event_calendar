import pytest
from rest_framework import status

from tests.factories import NotificationFactory


@pytest.mark.django_db
class TestNotificationAPI:
    def test_list_notifications(self, authenticated_client, user):
        NotificationFactory.create_batch(3, recipient=user)
        response = authenticated_client.get('/api/notifications/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_mark_as_read(self, authenticated_client, user):
        notification = NotificationFactory(recipient=user)
        response = authenticated_client.post(
            f'/api/notifications/{notification.id}/mark_as_read/'
        )
        assert response.status_code == status.HTTP_200_OK
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_mark_all_as_read(self, authenticated_client, user):
        NotificationFactory.create_batch(
            3,
            recipient=user,
            is_read=False
        )
        response = authenticated_client.post(
            '/api/notifications/mark_all_as_read/', user=user
        )
        assert response.status_code == status.HTTP_200_OK
        assert user.notifications.filter(is_read=False).count() == 0
