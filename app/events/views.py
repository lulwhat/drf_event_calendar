from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import transaction
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from events.filters import EventFilter
from events.models import Event, Reservation, Rating, Tag
from events.serializers import EventSerializer, ReservationSerializer, \
    RatingSerializer, TagSerializer, UserLoginSerializer, \
    UserRegisterSerializer
from events.tasks import send_booking_notification, \
    send_cancellation_notification


class IsOrganizerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user


class UserLoginView(GenericAPIView):
    """
    User authentication (token issuance).
    """
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            "access_token": str(access_token),
            "refresh_token": str(refresh),
            "user_id": user.pk,
            "email": user.email,
            "username": user.username
        })


class UserRegisterView(GenericAPIView):
    """
    Register a new user and return JWT tokens.
    """
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        email = serializer.validated_data.get('email', '')

        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'user_id': user.pk,
            'username': user.username,
            'email': user.email
        }, status=status.HTTP_201_CREATED)


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsOrganizerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter,
                       filters.SearchFilter]
    filterset_class = EventFilter
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['start_time', 'created_at', 'available_seats']
    queryset = Event.objects.with_annotations()

    def get_queryset(self):
        queryset = self.queryset.select_related(
            'organizer'
        )
        search_query = self.request.query_params.get('search')

        if search_query and hasattr(Event, 'search_vector'):
            queryset = queryset.annotate(
                rank=SearchRank('search_vector', SearchQuery(search_query))
            ).filter(search_vector=SearchQuery(search_query)).order_by('-rank')

        min_rating = self.request.query_params.get('min_organizer_rating')
        if min_rating:
            try:
                min_rating = float(min_rating)
                organizers = User.objects.annotate(
                    avg_rating=Avg('organized_events__ratings__rating')
                ).filter(avg_rating__gte=min_rating).values_list(
                    'id', flat=True
                )
                queryset = queryset.filter(organizer_id__in=organizers)
            except (ValueError, TypeError):
                pass

        tag_ids = self.request.query_params.getlist('tags')
        if tag_ids:
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()

        ordering = self.request.query_params.get('ordering')
        if ordering in self.ordering_fields:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('start_time')

        return queryset.all()

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    def destroy(self, request, *args, **kwargs):
        event = self.get_object()
        if not event.can_be_deleted():
            return Response(
                {"detail": "Events can only be deleted "
                           "within 1 hour of creation."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        event = self.get_object()
        if event.organizer != request.user:
            return Response({"detail": "Only the organizer can change "
                                       "the event status."},
                            status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        if new_status not in [s[0] for s in Event.STATUS_CHOICES]:
            return Response({"detail": "Invalid status value."},
                            status=status.HTTP_400_BAD_REQUEST)

        if new_status == 'cancelled' and event.status != 'cancelled':
            reservations = Reservation.objects.filter(
                event=event, status='confirmed'
            )
            for r in reservations:
                send_cancellation_notification.delay(r.id)

        event.status = new_status
        event.save()
        return Response(EventSerializer(instance=event).data)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def book(self, request, pk=None):
        event = self.get_object()

        if event.status != 'upcoming':
            return Response({"detail": "You can only book upcoming events."},
                            status=status.HTTP_400_BAD_REQUEST)

        available_seats = (
                event.available_seats - event.confirmed_reservations_count
        )

        if available_seats <= 0:
            return Response({"detail": "No available seats for this event."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                reservation, created = (Reservation.objects
                    .select_for_update()
                    .get_or_create(
                        user=request.user,
                        event=event, defaults={'status': 'confirmed'}
                    )
                )

                if not created:
                    if reservation.status == 'confirmed':
                        return Response(
                            {"detail": "You already have a "
                                       "confirmed reservation."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    reservation.status = 'confirmed'
                    reservation.save()

                send_booking_notification.delay(reservation.id)
                return Response(ReservationSerializer(reservation).data)
        except Exception as e:
            return Response({"detail": f"Failed to create reservation: {e}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def cancel_reservation(self, request, pk=None):
        event = self.get_object()
        try:
            reservation = Reservation.objects.get(
                user=request.user, event=event
            )
        except Reservation.DoesNotExist:
            return Response({"detail": "No reservation found."},
                            status=status.HTTP_404_NOT_FOUND)

        if reservation.status == 'cancelled':
            return Response({"detail": "Already cancelled."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                reservation.status = 'cancelled'
                reservation.save()
                updated = Reservation.objects.select_related(
                    'user', 'event'
                ).get(id=reservation.id)
                return Response(ReservationSerializer(updated).data)
        except Exception as e:
            return Response({"detail": f"Failed to cancel: {e}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def rate(self, request, pk=None):
        event = self.get_object()

        rating_data = {
            'rating': request.data.get('rating'),
            'comment': request.data.get('comment', ''),
            'event': event.id
        }

        serializer = RatingSerializer(
            data=rating_data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        if not Reservation.objects.filter(
                user=request.user, event=event, status='confirmed'
        ).exists():
            return Response(
                {"detail": "You can only rate events you participated in."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            with transaction.atomic():
                rating, _ = Rating.objects.update_or_create(
                    user=request.user,
                    event=event,
                    defaults={
                        'rating': request.data.get('rating'),
                        'comment': request.data.get('comment', '')
                    }
                )
                return Response(
                    RatingSerializer(rating, context={'request': request}).data
                )
        except Exception as e:
            return Response({"detail": f"Failed to rate event: {e}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        events = self.get_queryset().filter(
            reservations__user=request.user,
            reservations__status='confirmed'
        ).distinct()

        if request.query_params.get('upcoming') == 'true':
            events = events.filter(status='upcoming')

        return Response(self.get_serializer(events, many=True).data)

    @action(detail=False, methods=['get'])
    def organized(self, request):
        events = self.get_queryset().filter(
            organizer=request.user
        ).order_by('start_time')
        return Response(self.get_serializer(events, many=True).data)


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reservation.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    queryset = Tag.objects.all()
