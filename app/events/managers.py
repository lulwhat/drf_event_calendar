from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class EventManager(models.Manager):
    def with_annotations(self):
        """Queryset with all annotations"""
        return self.get_queryset().select_related('organizer').annotate(
            _confirmed_reservations_count=models.Count(
                'reservations__id',
                filter=models.Q(reservations__status='confirmed'),
                distinct=True
            ),
            _available_seats_count=models.F('available_seats') - models.Count(
                'reservations__id',
                filter=models.Q(reservations__status='confirmed'),
                distinct=True
            ),
            _average_rating=models.Avg('ratings__rating')
        )

    def get_queryset(self):
        """Base queryset without annotations"""
        return super().get_queryset().prefetch_related(
            'tags', 'reservations', 'ratings'
        )

    def get_or_none(self, *args, **kwargs):
        """Get with annotations or None"""
        qs = self.with_annotations()
        try:
            return qs.get(*args, **kwargs)
        except ObjectDoesNotExist:
            return None


class ReservationManager(models.Manager):
    def get_queryset(self):
        """Base queryset with related fields:
        - user
        - event
        - event__tags
        """
        return super().get_queryset().select_related(
            'user', 'event'
        ).prefetch_related(
            'event__tags'
        )

    def get_or_none(self, *args, **kwargs):
        """
        Returns Reservation instance if exists, otherwise returns None.
        Automatically includes all related fields (user, event, event.tags).
        """
        try:
            return self.get_queryset().get(*args, **kwargs)
        except ObjectDoesNotExist:
            return None


class RatingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user', 'event'
        )
