from django.contrib import admin

from events.models import Event, Tag, Reservation, Rating

admin.site.register(Event)
admin.site.register(Tag)
admin.site.register(Reservation)
admin.site.register(Rating)
