from datetime import timedelta

import pytest
from django.utils import timezone

from tests.factories import EventFactory, TagFactory, ReservationFactory


@pytest.mark.django_db
class TestEventModel:
    def test_event_creation(self):
        event = EventFactory()
        assert event.pk is not None
        assert event.status == 'upcoming'

    def test_available_seats_count(self):
        event = EventFactory(available_seats=10)
        ReservationFactory.create_batch(3, event=event, status='confirmed')
        assert event.available_seats_count == 7

    def test_can_be_deleted(self):
        event = EventFactory()
        assert event.can_be_deleted() is True

        # Mock created_at to be older than 1 hour
        event.created_at = timezone.now() - timedelta(hours=2)
        assert event.can_be_deleted() is False

    def test_tags_relationship(self):
        tag1 = TagFactory()
        tag2 = TagFactory()
        event = EventFactory(tags=[tag1, tag2])
        assert event.tags.count() == 2
        assert tag1.events.count() == 1


@pytest.mark.django_db
class TestReservationModel:
    def test_reservation_creation(self):
        reservation = ReservationFactory()
        assert reservation.pk is not None
        assert reservation.status == 'confirmed'

    def test_unique_together_constraint(self):
        reservation = ReservationFactory()
        with pytest.raises(Exception):
            ReservationFactory(user=reservation.user, event=reservation.event)
