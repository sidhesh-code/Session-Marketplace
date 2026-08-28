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

    def test_user_post_creator_session_returns_403(self):
        """Test 1 & 2: USER -> POST creator session endpoint -> 403 Forbidden"""
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

    def test_creator_post_creator_session_returns_201(self):
        """Test 3: CREATOR -> POST creator session endpoint -> 201 Created"""
        self.client.force_authenticate(user=self.creator1)
        url = reverse('creator-session-list')
        data = {
            "title": "New Session",
            "description": "New Desc",
            "start_time": (timezone.now() + timedelta(days=2)).isoformat(),
            "duration": 45,
            "capacity": 15
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "New Session")
        self.assertEqual(response.data['creator']['email'], self.creator1.email)

    def test_creator_edit_own_session_returns_200(self):
        """Test 3: CREATOR -> edit own session -> 200 OK"""
        self.client.force_authenticate(user=self.creator1)
        url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        data = {"title": "Updated Title By Owner"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Updated Title By Owner")
        self.session1.refresh_from_db()
        self.assertEqual(self.session1.title, "Updated Title By Owner")

    def test_creator_get_own_session_detail_returns_200(self):
        """Test 3: CREATOR -> GET own session detail -> 200 OK"""
        self.client.force_authenticate(user=self.creator1)
        url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.session1.id)

    def test_creator_a_edit_creator_b_session_returns_403(self):
        """Test 4: CREATOR A (creator2) -> edit CREATOR B (creator1) session -> 403 Forbidden"""
        self.client.force_authenticate(user=self.creator2)
        url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        data = {"title": "Malicious Title Edit"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creator_a_delete_creator_b_session_returns_403(self):
        """Test 4: CREATOR A (creator2) -> delete CREATOR B (creator1) session -> 403 Forbidden"""
        self.client.force_authenticate(user=self.creator2)
        url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Session.objects.filter(id=self.session1.id).exists())

    def test_creator_a_get_creator_b_session_returns_403(self):
        """Test 9: Object-level authorization: CREATOR A -> GET CREATOR B session via creator-detail endpoint -> 403 Forbidden"""
        self.client.force_authenticate(user=self.creator2)
        url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_access_creator_endpoints(self):
        """Test 1: USER -> creator endpoints (GET list, GET detail, PATCH, DELETE) -> 403 Forbidden"""
        self.client.force_authenticate(user=self.user)
        
        # GET /api/creator/sessions/ -> 403
        list_url = reverse('creator-session-list')
        list_resp = self.client.get(list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_403_FORBIDDEN)

        # GET /api/creator/sessions/<id>/ -> 403
        detail_url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        get_resp = self.client.get(detail_url)
        self.assertEqual(get_resp.status_code, status.HTTP_403_FORBIDDEN)

        # PATCH /api/creator/sessions/<id>/ -> 403
        patch_resp = self.client.patch(detail_url, {"title": "User Edit"}, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_403_FORBIDDEN)

        # DELETE /api/creator/sessions/<id>/ -> 403
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_access_creator_endpoints(self):
        """Test 6: Unauthenticated client -> creator endpoints -> 401 Unauthorized"""
        # GET /api/creator/sessions/ -> 401
        list_url = reverse('creator-session-list')
        list_resp = self.client.get(list_url)
        self.assertEqual(list_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # POST /api/creator/sessions/ -> 401
        post_resp = self.client.post(list_url, {"title": "Test"}, format='json')
        self.assertEqual(post_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # GET /api/creator/sessions/<id>/ -> 401
        detail_url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        get_resp = self.client.get(detail_url)
        self.assertEqual(get_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # PATCH /api/creator/sessions/<id>/ -> 401
        patch_resp = self.client.patch(detail_url, {"title": "Test"}, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # DELETE /api/creator/sessions/<id>/ -> 401
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creator_session_creation_ignores_client_supplied_creator(self):
        """Test 8: Role/Identity tampering: Creator passes creator_id in payload, server enforces request.user"""
        self.client.force_authenticate(user=self.creator1)
        url = reverse('creator-session-list')
        data = {
            "title": "Spoof Creator Session",
            "description": "Desc",
            "start_time": (timezone.now() + timedelta(days=3)).isoformat(),
            "duration": 60,
            "capacity": 10,
            "creator": self.creator2.id,
            "creator_id": self.creator2.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['creator']['email'], self.creator1.email)
        created_session = Session.objects.get(id=response.data['id'])
        self.assertEqual(created_session.creator, self.creator1)

    def test_creator_can_delete_own_session(self):
        """Test 3: CREATOR -> delete own session -> 204 No Content"""
        self.client.force_authenticate(user=self.creator1)
        detail_url = reverse('creator-session-detail', kwargs={'pk': self.session1.id})
        delete_resp = self.client.delete(detail_url)
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Session.objects.filter(id=self.session1.id).exists())
