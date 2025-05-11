import pytest
from rest_framework import status

from tests.factories import EventFactory, ReservationFactory, UserFactory


@pytest.mark.django_db
class TestReservationAPI:
    def test_list_reservations(self, authenticated_client, user):
        ReservationFactory.create_batch(3, user=user)
        response = authenticated_client.get('/api/reservations/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 3

    def test_create_reservation(self, authenticated_client, user):
        event = EventFactory(available_seats=5)
        data = {'event_id': event.id}
        response = authenticated_client.post('/api/reservations/', data=data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == 'confirmed'

    def test_cancel_reservation(self, authenticated_client, user):
        event = EventFactory(available_seats=5, status='upcoming')
        reservation = ReservationFactory(
            user=user,
            status='confirmed',
            event=event
        )
        response = authenticated_client.patch(
            f'/api/reservations/{reservation.id}/',
            data={'status': 'cancelled'}
        )
        assert response.status_code == status.HTTP_200_OK
        reservation.refresh_from_db()
        assert reservation.status == 'cancelled'

    def test_cannot_cancel_others_reservation(self, authenticated_client,
                                              user):
        other_user = UserFactory()
        event = EventFactory(available_seats=5)
        reservation = ReservationFactory(user=other_user, event=event)

        response = authenticated_client.patch(
            f'/api/reservations/{reservation.id}/',
            data={'status': 'cancelled'}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
