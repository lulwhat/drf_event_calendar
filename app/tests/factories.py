from datetime import timedelta

import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

from events.models import Event, Tag, Reservation, Rating
from notifications.models import Notification

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create and results:
            instance.save()


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda n: f'tag{n}')


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: f'Event {n}')
    description = factory.Faker('paragraph')
    start_time = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=1)
    )
    location = factory.Faker('city')
    available_seats = 10
    status = 'upcoming'
    organizer = factory.SubFactory(UserFactory)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create and results:
            instance.save()


class ReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reservation

    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
    status = 'confirmed'


class RatingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rating

    user = factory.SubFactory(UserFactory)
    event = factory.SubFactory(EventFactory)
    rating = 5
    comment = factory.Faker('paragraph')


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    notification_type = 'booking'
    title = factory.Faker('sentence')
    message = factory.Faker('paragraph')
    status = 'pending'
    is_read = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        notification = super()._create(model_class, *args, **kwargs)
        notification.refresh_from_db()
        return notification
