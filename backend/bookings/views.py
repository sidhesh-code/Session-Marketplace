from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db import models

from bookings.models import Booking
from bookings.serializers import BookingSerializer
from bookings.services import book_session, cancel_booking

from accounts.permissions import IsUserRole

class BookSessionView(APIView):
    permission_classes = [IsUserRole]

    def post(self, request, session_id):
        booking = book_session(request.user, session_id)
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class BookingListView(APIView):
    permission_classes = [IsUserRole]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).select_related('session', 'session__creator')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

class ActiveBookingListView(APIView):
    permission_classes = [IsUserRole]

    def get(self, request):
        now = timezone.now()
        bookings = Booking.objects.filter(
            user=request.user,
            status=Booking.Status.ACTIVE,
            session__start_time__gt=now
        ).select_related('session', 'session__creator')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

class PastBookingListView(APIView):
    permission_classes = [IsUserRole]

    def get(self, request):
        now = timezone.now()
        bookings = Booking.objects.filter(
            user=request.user
        ).filter(
            models.Q(status=Booking.Status.CANCELLED) | models.Q(session__start_time__lte=now)
        ).select_related('session', 'session__creator')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

class CancelBookingView(APIView):
    permission_classes = [IsUserRole]

    def post(self, request, pk):
        booking = cancel_booking(request.user, pk)
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
