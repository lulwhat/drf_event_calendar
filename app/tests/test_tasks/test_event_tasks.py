from datetime import timedelta

import pytest
from django.utils import timezone

from events.tasks import update_event_statuses, send_booking_notification
from tests.factories import EventFactory, ReservationFactory


@pytest.mark.django_db(transaction=True)
class TestEventTasks:
    def test_update_event_statuses_unit(self):
        # Create event that should be marked as completed
        old_event = EventFactory(
            status='upcoming',
            start_time=timezone.now() - timedelta(hours=3)
        )
        # Create event that should stay upcoming
        new_event = EventFactory(
            status='upcoming',
            start_time=timezone.now() + timedelta(hours=1)
        )

        result = update_event_statuses()
        assert 'Updated 1 events' in result

        old_event.refresh_from_db()
        new_event.refresh_from_db()
        assert old_event.status == 'completed'
        assert new_event.status == 'upcoming'

    def test_send_booking_notification(self, mocker):
        reservation = ReservationFactory()
        reservation.save()
        mocker.patch(
            'notifications.tasks.send_notification_via_grpc'
        )

        result = send_booking_notification.delay(reservation.id).get()
        assert "Booking notification created" in result
