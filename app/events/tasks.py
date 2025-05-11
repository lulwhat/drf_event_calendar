from datetime import timedelta

from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from events.models import Event, Reservation
from notifications.models import Notification
from notifications.tasks import send_notification_via_grpc


@shared_task(queue='default')
def update_event_statuses():
    """
    Update event statuses from 'upcoming' to 'completed'
    if 2 hours have passed since the event's start time.
    """
    try:
        two_hours_ago = timezone.now() - timedelta(hours=2)

        events = Event.objects.filter(
            status='upcoming',
            start_time__lte=two_hours_ago
        )
        updated_events_count = events.update(status='completed')

        return f'Updated {updated_events_count} events to "completed" status'
    except Exception as e:
        return f'"Failed to update events to "completed" with: {e}"'


@shared_task(queue='high_priority')
def send_booking_notification(reservation_id):
    """Send notification when a user books an event"""
    try:
        reservation = Reservation.objects.get_or_none(id=reservation_id)

        if reservation is None:
            return f'Reservation with {reservation_id} id not found'

        notification = Notification.objects.create(
            recipient_id=reservation.user.id,
            notification_type='booking',
            status='pending',
            title=f'Booking: {reservation.event.name}',
            message=f'Booked for {reservation.event.start_time}',
            object_id=reservation.event.id,
            content_object=reservation.event
        )
        send_notification_via_grpc.delay(notification.id)

        return f'Booking notification created with ID {notification.id}'
    except Exception as e:
        return (f'Failed to send {reservation_id} '
                f'booking notification with: {e}')


@shared_task(queue='high_priority')
def send_cancellation_notification(reservation_id):
    """Send notification when an event is cancelled"""
    try:
        reservation = Reservation.objects.get_or_none(id=reservation_id)
        if not reservation:
            return f'Reservation with {reservation_id} id not found'

        notification = Notification.objects.create(
            recipient_id=reservation.user.id,
            notification_type='cancellation',
            title=f'Event cancelled: {reservation.event.name}',
            message=f'The event {reservation.event.name} scheduled for '
                    f'{reservation.event.start_time} has been cancelled.',
            status='pending',
            created_at=timezone.now(),
            object_id=reservation.event.id,
            content_object=reservation.event
        )

        send_notification_via_grpc.delay(notification.id)

        return f'Cancellation notification created with ID {notification.id}'
    except Exception as e:
        return (f'Failed to send {reservation_id}'
                f' cancellation notification with: {e}')


@shared_task(queue='high_priority')
def send_event_reminders():
    """Send reminders to participants 1 hour before events"""
    try:
        one_hour_from_now = timezone.now() + timedelta(hours=1)
        two_hours_from_now = timezone.now() + timedelta(hours=2)

        events_to_remind = Reservation.objects.filter(
            event__status='upcoming',
            event__start_time__range=(one_hour_from_now, two_hours_from_now),
            status='confirmed'
        )

        event_content_type = ContentType.objects.get_for_model(Event)
        notifications = [
            Notification(
                recipient_id=row.user.id,
                notification_type='reminder',
                title=f'Reminder: {row.event.name}',
                status='pending',
                message=f'Your event {row.event.name} '
                        f'is starting in about 1 hour.',
                created_at=timezone.now(),
                object_id=row.event.id,
                content_type_id=event_content_type.id,
            )
            for row in events_to_remind
        ]

        created_notifications = Notification.objects.bulk_create(notifications)

        for notification in created_notifications:
            send_notification_via_grpc.delay(notification.id)

        return f'Sent {len(events_to_remind)} event reminders'
    except Exception as e:
        return f'Failed to send event reminders with: {e}'
