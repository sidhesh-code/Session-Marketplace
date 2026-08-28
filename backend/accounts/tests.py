import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import User

@pytest.mark.django_db
class TestAccounts:
    def setup_method(self):
        self.client = APIClient()

    def test_dev_login_user_creation(self):
        url = reverse('dev-login')
        data = {
            "email": "user@example.com",
            "name": "Regular User",
            "role": "USER"
        }
        response = self.client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['role'] == 'USER'

    def test_unauthenticated_profile_access_denied(self):
        url = reverse('profile-detail')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_profile_update(self):
        user = User.objects.create_user(email="test@example.com", name="Initial Name", role=User.Role.USER)
        self.client.force_authenticate(user=user)
        
        url = reverse('profile-detail')
        patch_data = {"name": "Updated Name"}
        response = self.client.patch(url, patch_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == "Updated Name"
