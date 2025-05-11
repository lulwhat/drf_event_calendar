import time
from unittest.mock import patch

import pytest

from notifications.models import Notification
from notifications.tasks import send_notification_via_grpc
from tests.factories import NotificationFactory


@pytest.mark.django_db
class TestNotificationTasks:
    def test_send_notification_via_grpc(self, mocker):
        # Create notification and check status
        notification = NotificationFactory()
        notification.save()
        notification.refresh_from_db()
        assert notification.status == 'pending'

        # Mock gRPC components
        mocker.patch('grpc.insecure_channel')
        mock_stub = mocker.patch(
            'grpc_server.notifications_pb2_grpc.NotificationServiceStub'
        )

        # Set successful response
        mock_response = mocker.Mock()
        mock_response.success = True
        mock_stub.return_value.SendNotification.return_value = mock_response

        result = send_notification_via_grpc.delay(notification.id).get()

        # Check results
        assert f"Notification {notification.id} sent via gRPC" in result
        notification.refresh_from_db()
        assert notification.status == 'sent'

    @patch('grpc.insecure_channel')
    def test_send_notification_failure_task(self, mock_channel):
        notification = NotificationFactory(status='pending')
        notification.save()

        assert Notification.objects.filter(id=notification.id).exists()
        assert notification.status == 'pending'

        # Mock gRPC exception
        mock_channel.side_effect = Exception("Connection failed")

        result = send_notification_via_grpc.delay(notification.id)

        # Add sleep to make sure task is executed and check multiple times
        for _ in range(10):
            try:
                task_result = result.get(timeout=0.1)
                break
            except Exception:
                time.sleep(0.1)
        else:
            pytest.fail("Task didn't complete in time")

        # Check results
        assert "Exception while sending" in task_result
        notification.refresh_from_db()
        assert notification.status == 'failed'
