from unittest.mock import patch

import pytest

from tests.factories import EventFactory, ReservationFactory


@pytest.mark.django_db
class TestNotificationFlow:
    @patch('events.views.send_cancellation_notification.delay')
    def test_notifications_on_event_cancellation(self, mock_task,
                                                 authenticated_client, user):
        event = EventFactory(organizer=user)
        reservations = ReservationFactory.create_batch(
            3, event=event, status='confirmed'
        )

        reservation_ids = [r.id for r in reservations]

        response = authenticated_client.post(
            f'/api/events/{event.id}/change_status/',
            {'status': 'cancelled'}
        )
        assert response.status_code == 200

        assert mock_task.call_count == 3

        called_ids = [args[0] for args, _ in mock_task.call_args_list]
        assert set(called_ids) == set(reservation_ids)
