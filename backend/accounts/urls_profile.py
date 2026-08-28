from django.urls import path
from accounts.views import ProfileView

urlpatterns = [
    path('', ProfileView.as_view(), name='profile-detail'),
]
