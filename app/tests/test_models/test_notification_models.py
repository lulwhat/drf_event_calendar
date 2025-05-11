import pytest

from tests.factories import NotificationFactory


@pytest.mark.django_db
class TestNotificationModel:
    def test_notification_creation(self):
        notification = NotificationFactory()
        assert notification.pk is not None
        assert notification.status == 'pending'
