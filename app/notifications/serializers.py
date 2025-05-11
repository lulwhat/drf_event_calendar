from rest_framework import serializers
from notifications.models import Notification
from events.serializers import UserSerializer


class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'notification_type', 'title',
            'message', 'status', 'created_at', 'sent_at'
        ]
        read_only_fields = ['recipient', 'status', 'created_at', 'sent_at']
