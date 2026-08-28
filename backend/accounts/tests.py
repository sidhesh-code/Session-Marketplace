from unittest.mock import patch, MagicMock
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from accounts.models import User

class AccountsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_dev_login_user_creation(self):
        url = reverse('dev-login')
        data = {
            "email": "user@example.com",
            "name": "Regular User",
            "role": "USER"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'USER')

    def test_dev_login_creator_creation(self):
        url = reverse('dev-login')
        data = {
            "email": "creator@example.com",
            "name": "Creator User",
            "role": "CREATOR"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'CREATOR')

    def test_unauthenticated_profile_access_denied(self):
        """Test 3: Missing access token returns 401 Unauthorized"""
        url = reverse('profile-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_jwt_token_returns_401(self):
        """Test 1: Malformed / invalid JWT token returns 401 Unauthorized"""
        url = reverse('profile-detail')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.corrupted.jwt.token')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_jwt_token_returns_401(self):
        """Test 2: Expired JWT token returns 401 Unauthorized"""
        user = User.objects.create_user(email="expired_test@example.com", name="Expired Test", role=User.Role.USER)
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        # Backdate token expiration
        access_token.set_exp(lifetime=-timedelta(minutes=10))
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')
        url = reverse('profile-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_flow(self):
        """Test 7: Valid refresh token issues new valid access token"""
        user = User.objects.create_user(email="refresh_test@example.com", name="Refresh Test", role=User.Role.USER)
        refresh = RefreshToken.for_user(user)
        
        url = reverse('token-refresh')
        response = self.client.post(url, {"refresh": str(refresh)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

        # Authenticate with newly refreshed access token
        new_access = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access}')
        profile_resp = self.client.get(reverse('profile-detail'))
        self.assertEqual(profile_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_resp.data['email'], "refresh_test@example.com")

    def test_invalid_refresh_token_returns_401(self):
        """Test 7: Malformed / invalid refresh token returns 401 Unauthorized"""
        url = reverse('token-refresh')
        response = self.client.post(url, {"refresh": "invalid.refresh.token"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_profile_update(self):
        user = User.objects.create_user(email="test@example.com", name="Initial Name", role=User.Role.USER)
        self.client.force_authenticate(user=user)
        
        url = reverse('profile-detail')
        patch_data = {"name": "Updated Name"}
        response = self.client.patch(url, patch_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Updated Name")

    def test_profile_patch_cannot_escalate_role(self):
        """Test: Profile PATCH cannot change role."""
        user = User.objects.create_user(email="user_escalate@example.com", name="Normal User", role=User.Role.USER)
        self.client.force_authenticate(user=user)

        url = reverse('profile-detail')
        patch_data = {"name": "Attempt Escalation", "role": "CREATOR"}
        response = self.client.patch(url, patch_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.role, User.Role.USER)
        self.assertEqual(user.name, "Attempt Escalation")

    def test_oauth_login_url_endpoint(self):
        url = reverse('oauth-url')
        response = self.client.get(url)
        # Should return 400 when unconfigured placeholder is present or 200 with auth_url when configured
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_oauth_callback_missing_code_returns_400(self):
        """Test 6: Missing authorization code returns 400 Bad Request"""
        url = reverse('oauth-callback')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Authorization code is required", response.data['detail'])

    @patch('accounts.views.requests.post')
    def test_oauth_callback_google_exchange_error_returns_400(self, mock_post):
        """Test 6: Google OAuth code exchange failure gracefully surfaces 400 Bad Request"""
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 400
        mock_token_resp.json.return_value = {"error": "invalid_grant", "error_description": "Code expired"}
        mock_post.return_value = mock_token_resp

        url = reverse('oauth-callback')
        response = self.client.post(url, {"code": "expired_or_invalid_code"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Failed to exchange Google OAuth code", response.data['detail'])

    @patch('accounts.views.requests.get')
    @patch('accounts.views.requests.post')
    def test_oauth_callback_google_userinfo_error_returns_400(self, mock_post, mock_get):
        """Test 6: Google userinfo fetch failure gracefully surfaces 400 Bad Request"""
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "valid_token"}
        mock_post.return_value = mock_token_resp

        mock_userinfo_resp = MagicMock()
        mock_userinfo_resp.status_code = 401
        mock_get.return_value = mock_userinfo_resp

        url = reverse('oauth-callback')
        response = self.client.post(url, {"code": "valid_code"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Failed to retrieve user info from Google", response.data['detail'])

    @patch('accounts.views.requests.get')
    @patch('accounts.views.requests.post')
    def test_oauth_new_user_login_creates_user_role(self, mock_post, mock_get):
        """Test: New Google USER login -> USER"""
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "google_test_access_token"}
        mock_post.return_value = mock_token_resp

        mock_userinfo_resp = MagicMock()
        mock_userinfo_resp.status_code = 200
        mock_userinfo_resp.json.return_value = {
            "email": "new_user@example.com",
            "name": "New User",
            "picture": "https://example.com/avatar.jpg"
        }
        mock_get.return_value = mock_userinfo_resp

        url = reverse('oauth-callback')
        response = self.client.post(url, {"code": "valid_google_code", "role": "USER"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], 'USER')
        
        created_user = User.objects.get(email="new_user@example.com")
        self.assertEqual(created_user.role, User.Role.USER)

    @patch('accounts.views.requests.get')
    @patch('accounts.views.requests.post')
    def test_oauth_new_creator_login_creates_creator_role(self, mock_post, mock_get):
        """Test: New Google CREATOR login -> CREATOR"""
        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "google_test_access_token"}
        mock_post.return_value = mock_token_resp

        mock_userinfo_resp = MagicMock()
        mock_userinfo_resp.status_code = 200
        mock_userinfo_resp.json.return_value = {
            "email": "new_creator@example.com",
            "name": "New Creator",
            "picture": "https://example.com/avatar.jpg"
        }
        mock_get.return_value = mock_userinfo_resp

        url = reverse('oauth-callback')
        response = self.client.post(url, {"code": "valid_google_code", "role": "CREATOR"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], 'CREATOR')
        
        created_user = User.objects.get(email="new_creator@example.com")
        self.assertEqual(created_user.role, User.Role.CREATOR)

    @patch('accounts.views.requests.get')
    @patch('accounts.views.requests.post')
    def test_oauth_existing_user_selecting_creator_becomes_creator(self, mock_post, mock_get):
        """Test: Existing USER selecting CREATOR -> becomes CREATOR"""
        existing_user = User.objects.create_user(
            email="existing_user@example.com",
            name="Existing User",
            role=User.Role.USER
        )

        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "google_test_access_token"}
        mock_post.return_value = mock_token_resp

        mock_userinfo_resp = MagicMock()
        mock_userinfo_resp.status_code = 200
        mock_userinfo_resp.json.return_value = {
            "email": "existing_user@example.com",
            "name": "Existing User",
            "picture": "https://example.com/avatar.jpg"
        }
        mock_get.return_value = mock_userinfo_resp

        url = reverse('oauth-callback')
        response = self.client.post(url, {"code": "valid_google_code", "role": "CREATOR"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], 'CREATOR')
        
        existing_user.refresh_from_db()
        self.assertEqual(existing_user.role, User.Role.CREATOR)

    @patch('accounts.views.requests.get')
    @patch('accounts.views.requests.post')
    def test_oauth_existing_creator_selecting_user_becomes_user(self, mock_post, mock_get):
        """Test: Existing CREATOR selecting USER -> becomes USER"""
        existing_creator = User.objects.create_user(
            email="existing_creator@example.com",
            name="Existing Creator",
            role=User.Role.CREATOR
        )

        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {"access_token": "google_test_access_token"}
        mock_post.return_value = mock_token_resp

        mock_userinfo_resp = MagicMock()
        mock_userinfo_resp.status_code = 200
        mock_userinfo_resp.json.return_value = {
            "email": "existing_creator@example.com",
            "name": "Existing Creator",
            "picture": "https://example.com/avatar.jpg"
        }
        mock_get.return_value = mock_userinfo_resp

        url = reverse('oauth-callback')
        response = self.client.post(url, {"code": "valid_google_code", "role": "USER"}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], 'USER')
        
        existing_creator.refresh_from_db()
        self.assertEqual(existing_creator.role, User.Role.USER)

    def test_oauth_invalid_role_rejected(self):
        """Test: Invalid role -> rejected with 400 Bad Request"""
        url = reverse('oauth-callback')
        response = self.client.post(url, {"code": "valid_google_code", "role": "ADMIN_SUPERUSER"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid role", response.data['detail'])
