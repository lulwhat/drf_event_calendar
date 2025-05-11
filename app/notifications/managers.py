from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class NotificationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('recipient')

    def get_or_none(self, *args, **kwargs):
        """
        Returns Notification instance if exists, otherwise returns None.
        """
        try:
            return self.get_queryset().get(*args, **kwargs)
        except ObjectDoesNotExist:
            return None
