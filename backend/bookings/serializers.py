from rest_framework import serializers
from bookings.models import Booking
from sessions_app.serializers import SessionSerializer
from accounts.serializers import UserSerializer

class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    session = SessionSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'user', 'session', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'session', 'status', 'created_at']
