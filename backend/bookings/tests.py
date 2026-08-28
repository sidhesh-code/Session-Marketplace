from django.test import TransactionTestCase
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

class BookingsTests(TransactionTestCase):
    def setUp(self):
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
        """Test: USER can book available sessions -> 201 Created"""
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        response = client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.filter(session=self.future_session, status='ACTIVE').count(), 1)

    def test_creator_cannot_book_session(self):
        """Test: CREATOR cannot book sessions -> 403 Forbidden"""
        client = APIClient()
        client.force_authenticate(user=self.creator)
        url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        response = client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_booking_endpoints(self):
        """Test: Unauthenticated access to booking endpoints returns 401 Unauthorized"""
        client = APIClient()
        book_url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        self.assertEqual(client.post(book_url).status_code, status.HTTP_401_UNAUTHORIZED)

        list_url = reverse('booking-list')
        self.assertEqual(client.get(list_url).status_code, status.HTTP_401_UNAUTHORIZED)

        active_url = reverse('booking-list-active')
        self.assertEqual(client.get(active_url).status_code, status.HTTP_401_UNAUTHORIZED)

        past_url = reverse('booking-list-past')
        self.assertEqual(client.get(past_url).status_code, status.HTTP_401_UNAUTHORIZED)

        cancel_url = reverse('booking-cancel', kwargs={'pk': 1})
        self.assertEqual(client.post(cancel_url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_cancel_own_booking(self):
        """Test: USER can cancel their own booking -> 200 OK, status CANCELLED"""
        booking = Booking.objects.create(user=self.user_a, session=self.future_session, status=Booking.Status.ACTIVE)
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('booking-cancel', kwargs={'pk': booking.id})
        response = client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)

    def test_user_cannot_cancel_another_users_booking(self):
        """Test: IDOR protection: User B cannot cancel User A's booking -> 404 Not Found"""
        booking = Booking.objects.create(user=self.user_a, session=self.future_session, status=Booking.Status.ACTIVE)
        client = APIClient()
        client.force_authenticate(user=self.user_b)
        url = reverse('booking-cancel', kwargs={'pk': booking.id})
        response = client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.ACTIVE)

    def test_cancelling_already_cancelled_booking_returns_400(self):
        """Test: Cancelling already cancelled booking -> 400 Bad Request"""
        booking = Booking.objects.create(user=self.user_a, session=self.future_session, status=Booking.Status.CANCELLED)
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('booking-cancel', kwargs={'pk': booking.id})
        response = client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_bookings_list_shows_only_own_bookings(self):
        """Test: User booking list isolation: User A sees only User A's bookings"""
        booking_a = Booking.objects.create(user=self.user_a, session=self.future_session, status=Booking.Status.ACTIVE)
        session_2 = Session.objects.create(
            creator=self.creator,
            title="Session 2",
            description="Desc",
            start_time=timezone.now() + timedelta(days=2),
            duration=45,
            capacity=10
        )
        booking_b = Booking.objects.create(user=self.user_b, session=session_2, status=Booking.Status.ACTIVE)

        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('booking-list')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking_ids = [b['id'] for b in response.data]
        self.assertIn(booking_a.id, booking_ids)
        self.assertNotIn(booking_b.id, booking_ids)

    def test_duplicate_active_booking_rejected(self):
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        
        # First booking succeeds
        resp1 = client.post(url)
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Duplicate active booking fails with 409 Conflict
        resp2 = client.post(url)
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already have an active booking", resp2.data['detail'])

    def test_booking_started_session_rejected(self):
        client = APIClient()
        client.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.started_session.id})
        
        response = client.post(url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already started", response.data['detail'])

    def test_booking_when_full_rejected(self):
        client_a = APIClient()
        client_a.force_authenticate(user=self.user_a)
        url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        
        # User A gets the only seat
        resp_a = client_a.post(url)
        self.assertEqual(resp_a.status_code, status.HTTP_201_CREATED)

        # User B attempts to book full session
        client_b = APIClient()
        client_b.force_authenticate(user=self.user_b)
        resp_b = client_b.post(url)
        self.assertEqual(resp_b.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("Session is full", resp_b.data['detail'])

    def test_booking_concurrency_capacity_1(self):
        """
        Concurrency Test (Capacity = 1):
        2 distinct users simultaneously book a single-seat session.
        Expected: exactly 1 Created (201), exactly 1 Conflict (409), active bookings count = 1.
        """
        session_id = self.future_session.id
        url = reverse('public-session-book', kwargs={'session_id': session_id})

        def make_booking(user):
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
        self.assertEqual(status_codes.count(status.HTTP_201_CREATED), 1)
        self.assertEqual(status_codes.count(status.HTTP_409_CONFLICT), 1)

        active_count = Booking.objects.filter(session_id=session_id, status='ACTIVE').count()
        self.assertEqual(active_count, 1)

    def test_booking_concurrency_capacity_multi_oversubscribed(self):
        """
        Concurrency Test (Capacity = 10 with 12 concurrent users):
        12 distinct users simultaneously attempt to book a 10-seat session.
        Expected: exactly 10 Created (201), exactly 2 Conflict (409), active bookings count = 10.
        """
        multi_session = Session.objects.create(
            creator=self.creator,
            title="High Capacity Session",
            description="Capacity 10 Concurrency Test",
            start_time=timezone.now() + timedelta(days=2),
            duration=60,
            capacity=10
        )
        session_id = multi_session.id
        url = reverse('public-session-book', kwargs={'session_id': session_id})

        # Create 12 distinct users
        users = [
            User.objects.create_user(email=f"concurrent_user_{i}@test.com", name=f"Concurrent {i}", role=User.Role.USER)
            for i in range(12)
        ]

        def make_booking(user):
            connection.close()
            client = APIClient()
            client.force_authenticate(user=user)
            return client.post(url)

        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = [executor.submit(make_booking, u) for u in users]
            results = [f.result() for f in futures]

        status_codes = [r.status_code for r in results]
        created_count = status_codes.count(status.HTTP_201_CREATED)
        conflict_count = status_codes.count(status.HTTP_409_CONFLICT)

        self.assertEqual(created_count, 10)
        self.assertEqual(conflict_count, 2)

        active_count = Booking.objects.filter(session_id=session_id, status='ACTIVE').count()
        self.assertEqual(active_count, 10)

    def test_booking_concurrency_same_user_duplicate(self):
        """
        Concurrency Test (Same User Duplicate Requests):
        The same user fires 2 concurrent booking requests against an available session.
        Expected: exactly 1 Created (201), exactly 1 Conflict (409), active bookings count = 1.
        """
        multi_session = Session.objects.create(
            creator=self.creator,
            title="Duplicate Test Session",
            description="Same user concurrency test",
            start_time=timezone.now() + timedelta(days=3),
            duration=45,
            capacity=10
        )
        session_id = multi_session.id
        url = reverse('public-session-book', kwargs={'session_id': session_id})

        def make_booking(user):
            connection.close()
            client = APIClient()
            client.force_authenticate(user=user)
            return client.post(url)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(make_booking, self.user_a)
            future2 = executor.submit(make_booking, self.user_a)
            
            res1 = future1.result()
            res2 = future2.result()

        status_codes = [res1.status_code, res2.status_code]
        self.assertEqual(status_codes.count(status.HTTP_201_CREATED), 1)
        self.assertEqual(status_codes.count(status.HTTP_409_CONFLICT), 1)

        active_count = Booking.objects.filter(session_id=session_id, user=self.user_a, status='ACTIVE').count()
        self.assertEqual(active_count, 1)

    def test_booking_concurrency_started_session(self):
        """
        Concurrency Test (Started Session):
        Concurrent requests against a session that already started all receive 409 Conflict.
        """
        session_id = self.started_session.id
        url = reverse('public-session-book', kwargs={'session_id': session_id})

        def make_booking(user):
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
        self.assertEqual(status_codes.count(status.HTTP_409_CONFLICT), 2)

        active_count = Booking.objects.filter(session_id=session_id, status='ACTIVE').count()
        self.assertEqual(active_count, 0)

    def test_cancellation_releases_seat_and_allows_rebooking(self):
        """
        Business Logic Test:
        Verifies that when a booking is cancelled, the seat is released and another user can book it.
        """
        client_a = APIClient()
        client_a.force_authenticate(user=self.user_a)
        book_url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})

        # 1. User A books the only seat
        resp_a = client_a.post(book_url)
        self.assertEqual(resp_a.status_code, status.HTTP_201_CREATED)
        booking_id = resp_a.data['id']

        # 2. User B tries to book -> rejected (Session full)
        client_b = APIClient()
        client_b.force_authenticate(user=self.user_b)
        resp_b_full = client_b.post(book_url)
        self.assertEqual(resp_b_full.status_code, status.HTTP_409_CONFLICT)

        # 3. User A cancels booking
        cancel_url = reverse('booking-cancel', kwargs={'pk': booking_id})
        cancel_resp = client_a.post(cancel_url)
        self.assertEqual(cancel_resp.status_code, status.HTTP_200_OK)

        # 4. User B now successfully books the freed seat
        resp_b_success = client_b.post(book_url)
        self.assertEqual(resp_b_success.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Booking.objects.filter(session=self.future_session, status='ACTIVE').count(), 1)

    def test_session_cascade_deletion_removes_bookings(self):
        """
        Business Logic Test:
        Verifies that deleting a session cleanly cascades and removes associated bookings.
        """
        client_a = APIClient()
        client_a.force_authenticate(user=self.user_a)
        book_url = reverse('public-session-book', kwargs={'session_id': self.future_session.id})
        resp = client_a.post(book_url)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        booking_id = resp.data['id']

        # Creator deletes the session
        creator_client = APIClient()
        creator_client.force_authenticate(user=self.creator)
        delete_url = reverse('creator-session-detail', kwargs={'pk': self.future_session.id})
        del_resp = creator_client.delete(delete_url)
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)

        # Verified booking is removed
        self.assertFalse(Booking.objects.filter(id=booking_id).exists())

