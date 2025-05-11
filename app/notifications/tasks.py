import grpc
from celery import shared_task

from grpc_server import notifications_pb2, notifications_pb2_grpc
from notifications.models import Notification


@shared_task(queue='high_priority')
def send_notification_via_grpc(notification_id):
    """
    Send notification via gRPC NotificationService
    """
    notification = Notification.objects.get_or_none(id=notification_id)

    if notification is None:
        return f'Notification {notification_id} not found'

    if notification.status != 'pending':
        return f'Notification {notification_id} is already processed'

    try:
        with grpc.insecure_channel('grpc:50051') as channel:
            stub = notifications_pb2_grpc.NotificationServiceStub(channel)

            request = notifications_pb2.NotificationRequest(
                recipient_id=notification.recipient_id,
                notification_type=notification.notification_type,
                title=notification.title,
                message=notification.message,
                related_object_type=getattr(
                    notification, 'related_object_type', ''
                ),
                related_object_id=notification.object_id
            )

            response = stub.SendNotification(request)

            if response.success:
                notification.status = 'sent'
                notification.save()
                return f'Notification {notification_id} sent via gRPC'
            else:
                notification.status = 'failed'
                notification.save()
                return f'gRPC error: {response.message}'

    except Exception as e:
        if notification:
            notification.status = 'failed'
            notification.save()
        return f'Exception while sending notification via gRPC: {str(e)}'
