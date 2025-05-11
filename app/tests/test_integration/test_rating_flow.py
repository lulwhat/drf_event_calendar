from datetime import timedelta

import pytest
from django.utils import timezone

from tests.factories import EventFactory, ReservationFactory


@pytest.mark.django_db
class TestRatingFlow:
    def test_rating_after_event_completion(
            self, authenticated_client, user, organizer
    ):
        event = EventFactory(
            status='completed',
            start_time=timezone.now() - timedelta(days=1),
            organizer=organizer
        )
        ReservationFactory(
            user=user,
            event=event,
            status='confirmed'
        )

        rating_data = {
            'rating': 5,
            'comment': 'Great event!'
        }
        response = authenticated_client.post(
            f'/api/events/{event.id}/rate/',
            rating_data
        )
        assert response.status_code == 200
        assert response.data['rating'] == 5

        event_response = authenticated_client.get(f'/api/events/{event.id}/')
        assert event_response.data['average_rating'] == 5.0
