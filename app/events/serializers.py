from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from events.models import Event, Reservation, Rating, Tag


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class RatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        write_only=True
    )

    class Meta:
        model = Rating
        fields = ['id', 'user', 'rating', 'comment', 'created_at', 'event']
        read_only_fields = ['user']

    def validate(self, data):
        event = data['event']
        user = self.context['request'].user

        if event.status != 'completed':
            raise serializers.ValidationError(
                "You can only rate completed events."
            )

        if not Reservation.objects.filter(
                user=user, event=event, status='confirmed'
        ).exists():
            raise serializers.ValidationError(
                "You can only rate events you participated in."
            )

        return data


class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='tags'
    )

    available_seats_count = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'start_time', 'location',
            'available_seats', 'available_seats_count', 'status',
            'organizer', 'created_at', 'tags', 'tag_ids', 'average_rating'
        ]
        read_only_fields = [
            'organizer', 'created_at',
            'available_seats_count', 'average_rating'
        ]

    def validate_start_time(self, value):
        if self.instance is None and value < timezone.now():
            raise serializers.ValidationError(
                "Start time cannot be in the past."
            )
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        event = Event.objects.create(**validated_data)
        if tags:
            event.tags.set(tags)
        return event

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        event = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags)
        return event


class ReservationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(),
        write_only=True,
        source='event',
        required=False
    )

    class Meta:
        model = Reservation
        fields = ['id', 'user', 'event', 'event_id', 'status', 'created_at']
        read_only_fields = ['user', 'event', 'created_at']

    def validate(self, data):
        user = self.context['request'].user
        instance = self.instance

        # Reservation create case
        if instance is None:
            event = data.get('event')
            if not event:
                raise serializers.ValidationError("Event is required")

            if event.status != 'upcoming':
                raise serializers.ValidationError(
                    "You can only book upcoming events.")

            if event.available_seats_count <= 0:
                raise serializers.ValidationError(
                    "No available seats for this event."
                )

            if Reservation.objects.filter(user=user, event=event).exists():
                raise serializers.ValidationError(
                    "You already have a reservation for this event."
                )

        # Reservation patch case
        else:
            if instance.user != user:
                raise serializers.ValidationError(
                    "You can only modify your own reservations."
                )

        return data
