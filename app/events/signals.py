from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector

from events.models import Event


@receiver(post_save, sender=Event)
def update_search_vector(sender, instance, **kwargs):
    Event.objects.filter(pk=instance.pk).update(
        search_vector=SearchVector('name', 'description', 'location')
    )
