from datetime import timedelta

import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestEventFullFlow:
    def test_event_lifecycle(self, authenticated_client):
        # Create event
        event_data = {
            'name': 'Integration Test Event',
            'description': 'Test',
            'start_time': (timezone.now() + timedelta(days=2)).isoformat(),
            'location': 'Test City',
            'available_seats': 5
        }
        create_response = authenticated_client.post('/api/events/', event_data)
        assert create_response.status_code == 201

        # Book event
        event_id = create_response.data['id']
        book_response = authenticated_client.post(
            f'/api/events/{event_id}/book/')
        assert book_response.status_code == 200

        # Cancel booking
        cancel_response = authenticated_client.post(
            f'/api/events/{event_id}/cancel_reservation/'
        )
        assert cancel_response.status_code == 200
