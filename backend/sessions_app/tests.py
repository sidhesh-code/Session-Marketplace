from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User
from sessions_app.models import Session

class SessionsAuthorizationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="user@test.com", name="User", role=User.Role.USER)
        self.creator1 = User.objects.create_user(email="creator1@test.com", name="Creator 1", role=User.Role.CREATOR)
        self.creator2 = User.objects.create_user(email="creator2@test.com", name="Creator 2", role=User.Role.CREATOR)

        self.session1 = Session.objects.create(
            creator=self.creator1,
            title="Creator 1 Session",
            description="Test Description",
            start_time=timezone.now() + timedelta(days=1),
            duration=60,
            capacity=5
        )

    def test_user_cannot_access_creator_endpoint(self):
        """Test 1: Normal USER attempts a creator-only endpoint (POST /api/creator/sessions/) -> 403"""
        self.client.force_authenticate(user=self.user)
        url = reverse('creator-session-list')
        data = {
            "title": "Unauthorized Session",
            "description": "Desc",
            "start_time": (timezone.now() + timedelta(days=1)).isoformat(),
            "duration": 60,
            "capacity": 10
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_cannot_edit_another_creators_session(self):
        """Test 2: Creator A (creator2) attempts to edit Creator B's (creator1) session -> 403"""
        self.client.force_authenticate(user=self.creator2)
        url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        data = {"title": "Hacked Title"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_can_create_and_edit_own_session(self):
        self.client.force_authenticate(user=self.creator1)
        url = reverse('creator-session-list')
        data = {
            "title": "New Session",
            "description": "New Desc",
            "start_time": (timezone.now() + timedelta(days=2)).isoformat(),
            "duration": 45,
            "capacity": 15
        }
        create_resp = self.client.post(url, data, format='json')
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)

        session_id = create_resp.data['id']
        detail_url = reverse('creator-session-detail', kwargs={'pk': session_id})
        edit_resp = self.client.patch(detail_url, {"title": "Updated Title"}, format='json')
        self.assertEqual(edit_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(edit_resp.data['title'], "Updated Title")

    def test_creator_can_delete_own_session(self):
        self.client.force_authenticate(user=self.creator1)
        detail_url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Session.objects.filter(id=self.session1.id).exists())
