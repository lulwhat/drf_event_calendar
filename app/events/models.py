from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from events.managers import EventManager, ReservationManager, RatingManager

DELETION_GRACE_PERIOD = 3600


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f'Tag {self.pk} - {self.name}'


class Event(models.Model):
    STATUS_CHOICES = (
        ('upcoming', 'Upcoming'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    location = models.CharField(max_length=100)  # City
    available_seats = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='upcoming')
    organizer = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='organized_events')
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, related_name='events', blank=True)
    search_vector = SearchVectorField(null=True)

    objects = EventManager()

    class Meta:
        ordering = [
            models.Case(
                models.When(status='upcoming', then=0),
                models.When(status='completed', then=1),
                models.When(status='cancelled', then=2),
                default=3,
                output_field=models.IntegerField(),
            ),
            'start_time'
        ]
        indexes = [
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['location']),
            models.Index(fields=['organizer']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Event {self.pk} - {self.name}'

    @property
    def confirmed_reservations_count(self):
        if hasattr(self, '_confirmed_reservations_count'):
            return self._confirmed_reservations_count
        return self.reservations.filter(status='confirmed').count()

    @property
    def available_seats_count(self):
        if hasattr(self, '_available_seats_count'):
            return self._available_seats_count
        return self.available_seats - self.confirmed_reservations_count

    @property
    def average_rating(self):
        if hasattr(self, '_average_rating'):
            return self._average_rating
        return self.ratings.aggregate(avg=models.Avg('rating'))['avg'] or 0

    def can_be_deleted(self):
        """Check if event can be deleted (within 1 hour of creation)"""
        return (
            timezone.now() - self.created_at
        ).total_seconds() <= DELETION_GRACE_PERIOD


class Reservation(models.Model):
    STATUS_CHOICES = (
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='reservations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='reservations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReservationManager()

    class Meta:
        unique_together = ('user', 'event')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['event', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at',]

    def __str__(self):
        return (f'Reservation {self.pk} - '
                f'by {self.user.username} for {self.event.name}')


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='ratings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              related_name='ratings')
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = RatingManager()

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return (f"Rating {self.pk} - "
                f"{self.user.username} rated {self.event.name}: {self.rating}")
