from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status

from tests.factories import EventFactory, TagFactory, ReservationFactory


@pytest.mark.django_db
class TestEventAPI:
    def test_list_events(self, authenticated_client):
        EventFactory.create_batch(3)
        response = authenticated_client.get('/api/events/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_create_event(self, authenticated_client, organizer):
        authenticated_client.force_authenticate(user=organizer)
        tag = TagFactory()
        data = {
            'name': 'New Event',
            'description': 'Event description',
            'start_time': (timezone.now() + timedelta(days=1)).isoformat(),
            'location': 'Test City',
            'available_seats': 10,
            'tags': [tag.id]
        }
        response = authenticated_client.post('/api/events/', data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['organizer']['id'] == organizer.id

    def test_update_event(self, authenticated_client, user):
        event = EventFactory(organizer=user)
        data = {'name': 'Updated Name'}
        response = authenticated_client.patch(
            f'/api/events/{event.id}/', data=data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_delete_event(self, authenticated_client, user):
        event = EventFactory(organizer=user)
        response = authenticated_client.delete(f'/api/events/{event.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_book_event(self, authenticated_client, user, organizer):
        event = EventFactory(available_seats=5, organizer=organizer)
        response = authenticated_client.post(
            f'/api/events/{event.id}/book/'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'confirmed'

    def test_cancel_reservation(self, authenticated_client, user):
        event = EventFactory()
        reservation = ReservationFactory(
            user=user,
            event=event,
            status='confirmed'
        )
        response = authenticated_client.post(
            f'/api/events/{event.id}/cancel_reservation/'
        )
        assert response.status_code == status.HTTP_200_OK
        reservation.refresh_from_db()
        assert reservation.status == 'cancelled'

    def test_rate_event(self, authenticated_client, user):
        event = EventFactory(status='completed')
        ReservationFactory(
            user=user,
            event=event,
            status='confirmed'
        )
        data = {'rating': 5, 'comment': 'Great event!'}
        response = authenticated_client.post(
            f'/api/events/{event.id}/rate/',
            data=data
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['rating'] == 5
