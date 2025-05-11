from unittest.mock import patch

import pytest

from notifications.models import Notification
from notifications.tasks import send_notification_via_grpc
from tests.factories import NotificationFactory


@pytest.mark.django_db
class TestGrpcIntegration:
    @patch('grpc.insecure_channel')
    @patch('grpc_server.notifications_pb2_grpc.NotificationServiceStub')
    def test_full_grpc_flow(self, mock_stub, mock_channel):
        notification = NotificationFactory(status='pending')
        notification.save()

        assert Notification.objects.filter(id=notification.id).exists()
        assert notification.status == 'pending'

        mock_response = type('Response', (), {
            'success': True,
            'message': 'OK'
        })()
        mock_stub.return_value.SendNotification.return_value = mock_response

        result = send_notification_via_grpc.delay(notification.id).get()
        assert 'sent via gRPC' in result

        notification.refresh_from_db()
        assert notification.status == 'sent'

        mock_stub.return_value.SendNotification.assert_called_once()
        args, _ = mock_stub.return_value.SendNotification.call_args
        assert args[0].recipient_id == notification.recipient_id
        assert args[0].title == notification.title
