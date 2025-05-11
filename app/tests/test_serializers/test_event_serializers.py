from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from events.serializers import EventSerializer, ReservationSerializer, \
    RatingSerializer
from tests.factories import EventFactory, TagFactory, ReservationFactory


@pytest.mark.django_db
class TestEventSerializer:
    def test_serialization(self):
        event = EventFactory()
        serializer = EventSerializer(event)
        assert serializer.data['id'] == event.id
        assert serializer.data['name'] == event.name

    def test_create_event(self, user):
        tag = TagFactory()
        data = {
            'name': 'New Event',
            'description': 'Description',
            'start_time': (timezone.now() + timedelta(days=1)).isoformat(),
            'location': 'Test City',
            'available_seats': 10,
            'tag_ids': [tag.id]
        }
        serializer = EventSerializer(data=data, context={'request': None})
        assert serializer.is_valid()
        event = serializer.save(organizer=user)
        assert event.tags.count() == 1

    def test_validate_start_time(self):
        data = {
            'name': 'New Event',
            'description': 'Description',
            'start_time': (timezone.now() - timedelta(days=1)).isoformat(),
            'location': 'Test City',
            'available_seats': 10
        }
        serializer = EventSerializer(data=data)
        assert not serializer.is_valid()
        assert 'start_time' in serializer.errors


@pytest.mark.django_db
class TestReservationSerializer:
    def test_validate(self, user):
        event = EventFactory(available_seats=1)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user

        serializer = ReservationSerializer(
            data={'event_id': event.id},
            context={'request': request}
        )
        assert serializer.is_valid()

    def test_validate_no_seats(self, user):
        event = EventFactory(available_seats=0)

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user

        serializer = ReservationSerializer(
            data={'event_id': event.id},
            context={'request': request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestRatingSerializer:
    def test_validate(self, user):
        event = EventFactory(status='completed')
        ReservationFactory(user=user, event=event, status='confirmed')

        factory = APIRequestFactory()
        request = factory.post('/')
        request.user = user

        data = {
            'rating': 5,
            'comment': 'Great!',
            'event': event.id
        }

        serializer = RatingSerializer(
            data=data,
            context={'request': request}
        )

        assert serializer.is_valid()

        validated_data = serializer.validated_data
        assert validated_data['rating'] == 5
        assert validated_data['comment'] == 'Great!'
        assert validated_data['event'] == event
