from unittest.mock import AsyncMock

import pytest
from grpc.aio import ServicerContext

from grpc_server import notifications_pb2
from grpc_server.grpc_server_main import NotificationServicer


@pytest.mark.asyncio
class TestGrpcServer:
    async def test_send_notification_success(self):
        servicer = NotificationServicer()
        request = notifications_pb2.NotificationRequest(
            recipient_id=1,
            notification_type='booking',
            title='Test',
            message='Test message'
        )

        response = await servicer.SendNotification(request, AsyncMock())
        assert response.success is True
        assert "successfully" in response.message

    async def test_send_notification_failure_grpc(self, mocker):
        mock_response = notifications_pb2.NotificationResponse(
            success=False,
            message="Test error"
        )

        servicer = NotificationServicer()
        servicer.SendNotification = AsyncMock(return_value=mock_response)

        request = notifications_pb2.NotificationRequest(
            recipient_id=1,
            notification_type='booking',
            title='Test',
            message='Test message'
        )

        mock_context = mocker.MagicMock(spec=ServicerContext)
        response = await servicer.SendNotification(request, mock_context)

        assert response.success is False
        assert "Test error" in response.message
