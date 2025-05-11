from django.urls import path, include
from rest_framework.routers import DefaultRouter
from events.views import EventViewSet, ReservationViewSet, TagViewSet

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
