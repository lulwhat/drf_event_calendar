from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from notifications.managers import NotificationManager


class Notification(models.Model):
    TYPE_CHOICES = (
        ('booking', 'Booking Confirmation'),
        ('cancellation', 'Event Cancellation'),
        ('reminder', 'Event Reminder'),
        ('event_update', 'Event Update'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default='pending')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    # Generic relation to the related object (Event, Reservation, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = NotificationManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return (f"Notification {self.pk} - {self.notification_type} "
                f"- {self.status}")
