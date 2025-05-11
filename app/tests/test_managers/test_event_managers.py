import pytest

from events.models import Event, Reservation
from tests.factories import EventFactory, ReservationFactory


@pytest.mark.django_db
class TestEventManager:
    def test_get_queryset_annotations(self):
        event = EventFactory()

        # Create 2 confirmed reservations
        ReservationFactory.create_batch(
            2, event=event, status='confirmed'
        )

        # Create 3 cancelled reservations to check filter
        ReservationFactory.create_batch(
            3, event=event, status='cancelled'
        )

        # Check in DB
        db_count = Reservation.objects.filter(
            event=event, status='confirmed'
        ).count()
        assert db_count == 2

        # Check annotated obj
        annotated_event = Event.objects.with_annotations().get(pk=event.pk)
        assert annotated_event._confirmed_reservations_count == 2

    def test_get_or_none(self):
        event = EventFactory()
        result = Event.objects.get_or_none(pk=event.pk)
        assert hasattr(result, '_confirmed_reservations_count')
        assert Event.objects.get_or_none(pk=99999) is None
