import pytest

from rest_framework.test import APIClient

from tests.factories import EventFactory, UserFactory


@pytest.mark.django_db
class TestBookingFlow:
    def test_concurrent_booking(self, authenticated_client):
        # Create event with 1 seat
        event = EventFactory(available_seats=1)

        # Imitate 2 requests in parallel
        client2 = APIClient()
        user2 = UserFactory(
            username='user2', email='user2@test.com', password='password'
        )
        client2.force_authenticate(user2)

        response1 = authenticated_client.post(f'/api/events/{event.id}/book/')
        response2 = client2.post(f'/api/events/{event.id}/book/')

        # Check only 1 booking is successful
        successful = 0
        if response1.status_code == 200:
            successful += 1
        if response2.status_code == 200:
            successful += 1

        assert successful == 1
        assert event.reservations.filter(status='confirmed').count() == 1
