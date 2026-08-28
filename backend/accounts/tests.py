from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
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

    def test_unauthenticated_profile_access_denied(self):
        url = reverse('profile-detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_profile_update(self):
        user = User.objects.create_user(email="test@example.com", name="Initial Name", role=User.Role.USER)
        self.client.force_authenticate(user=user)
        
        url = reverse('profile-detail')
        patch_data = {"name": "Updated Name"}
        response = self.client.patch(url, patch_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Updated Name")
