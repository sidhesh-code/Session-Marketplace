from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import status
from django.shortcuts import get_object_or_404

from sessions_app.models import Session
from bookings.models import Booking
from config.exceptions import BookingError

def book_session(user, session_id):
    """
    Executes a concurrency-safe session booking using PostgreSQL transaction row-level locking.
    
    Invariants protected:
    1. active_bookings <= session.capacity
    2. User cannot duplicate active bookings
    3. Session that has already started cannot be booked
    """
    with transaction.atomic():
        # Acquire exclusive PostgreSQL row-level lock on the target Session
        try:
            session = Session.objects.select_for_update().get(pk=session_id)
        except Session.DoesNotExist:
            raise BookingError("Session not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Invariant 3: Check whether session has already started
        if timezone.now() >= session.start_time:
            raise BookingError("Session has already started.", status_code=status.HTTP_409_CONFLICT)

        # Invariant 2: Check duplicate active booking
        existing_active = Booking.objects.filter(
            user=user,
            session=session,
            status=Booking.Status.ACTIVE
        ).exists()
        
        if existing_active:
            raise BookingError("You already have an active booking for this session.", status_code=status.HTTP_409_CONFLICT)

        # Invariant 1: Count active bookings and check capacity
        active_count = Booking.objects.filter(
            session=session,
            status=Booking.Status.ACTIVE
        ).count()

        if active_count >= session.capacity:
            raise BookingError("Session is full.", status_code=status.HTTP_409_CONFLICT)

        # Create active booking
        try:
            booking = Booking.objects.create(
                user=user,
                session=session,
                status=Booking.Status.ACTIVE
            )
            return booking
        except IntegrityError:
            # Catch DB-level partial unique constraint violations if triggered
            raise BookingError("You already have an active booking for this session.", status_code=status.HTTP_409_CONFLICT)

def cancel_booking(user, booking_id):
    """
    Allows a user to cancel their active booking.
    """
    with transaction.atomic():
        try:
            booking = Booking.objects.select_for_update().get(pk=booking_id, user=user)
        except Booking.DoesNotExist:
            raise BookingError("Booking not found or not owned by user.", status_code=status.HTTP_404_NOT_FOUND)

        if booking.status == Booking.Status.CANCELLED:
            raise BookingError("Booking is already cancelled.", status_code=status.HTTP_400_BAD_REQUEST)

        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=['status'])
        return booking
