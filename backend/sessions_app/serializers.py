from rest_framework import serializers
from django.utils import timezone
from sessions_app.models import Session
from accounts.serializers import UserSerializer

class SessionSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    booked_seats = serializers.SerializerMethodField()
    remaining_seats = serializers.SerializerMethodField()
    is_started = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = [
            'id', 'creator', 'title', 'description', 
            'start_time', 'duration', 'capacity', 
            'booked_seats', 'remaining_seats', 'is_started',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']

    def get_booked_seats(self, obj):
        # Return count of active bookings
        return obj.bookings.filter(status='ACTIVE').count()

    def get_remaining_seats(self, obj):
        active_count = self.get_booked_seats(obj)
        return max(0, obj.capacity - active_count)

    def get_is_started(self, obj):
        return timezone.now() >= obj.start_time

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be a positive integer greater than zero.")
        return value

    def validate_duration(self, value):
        if value <= 0:
            raise serializers.ValidationError("Duration must be greater than zero minutes.")
        return value
