import pytest
from concurrent.futures import ThreadPoolExecutor
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from django.db import connection

from accounts.models import User
from sessions_app.models import Session
from bookings.models import Booking

@pytest.mark.django_db(transaction=True)
class TestBookings:
    def setup_method(self):
        self.creator = User.objects.create_user(email="creator@test.com", name="Creator", role=User.Role.CREATOR)
        self.user_a = User.objects.create_user(email="usera@test.com", name="User A", role=User.Role.USER)
        self.user_b = User.objects.create_user(email="userb@test.com", name="User B", role=User.Role.USER)

        self.future_session = Session.objects.create(
            creator=self.creator,
            title="Future Session",
            description="Capacity 1 Test",
            start_time=timezone.now() + timedelta(days=1),
            duration=60,
            capacity=1
        )

        self.started_session = Session.objects.create(
            creator=self.creator,
            title="Started Session",
            description="Started Test",
            start_time=timezone.now() - timedelta(hours=1),
            duration=60,
            capacity=10
        )

    def test_successful_booking(self):
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        response = client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert Booking.objects.filter(session=self.future_session, status='ACTIVE').count() == 1

    def test_duplicate_active_booking_rejected(self):
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        
        # First booking succeeds
        resp1 = client.post(url)
        assert resp1.status_code == status.HTTP_201_CREATED

        # Duplicate active booking fails with 409 Conflict
        resp2 = client.post(url)
        assert resp2.status_code == status.HTTP_409_CONFLICT
        assert "already have an active booking" in resp2.data['detail']

    def test_booking_started_session_rejected(self):
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.started_session.id})
        
        response = client.post(url)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already started" in response.data['detail']

    def test_booking_when_full_rejected(self):
        client_a = APIClient()
        client_a.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        
        # User A gets the only seat
        resp_a = client_a.post(url)
        assert resp_a.status_code == status.HTTP_201_CREATED

        # User B attempts to book full session
        client_b = APIClient()
        client_b.force_authenticate(user=self.user_b)
        resp_b = client_b.post(url)
        assert resp_b.status_code == status.HTTP_409_CONFLICT
        assert "Session is full" in resp_b.data['detail']

    def test_booking_concurrency_postgresql(self):
        """
        Concurrency Test:
        Fires 2 booking requests concurrently against a capacity=1 session.
        Verifies that row locking prevents oversubscription:
        - 1 request returns 201 Created
        - 1 request returns 409 Conflict
        - Final active bookings count in DB == 1
        """
        session_id = self.future_session.id
        url = reverse('public-session-book', kwargs={'session_id': session_id})

        def make_booking(user):
            # Close existing connection to ensure separate thread DB connections
            connection.close()
            client = APIClient()
            client.force_authenticate(user=user)
            return client.post(url)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(make_booking, self.user_a)
            future2 = executor.submit(make_booking, self.user_b)
            
            res1 = future1.result()
            res2 = future2.result()

        status_codes = [res1.status_code, res2.status_code]
        assert status.HTTP_201_CREATED in status_codes
        assert status.HTTP_409_CONFLICT in status_codes

        active_count = Booking.objects.filter(session_id=session_id, status='ACTIVE').count()
        assert active_count == 1
