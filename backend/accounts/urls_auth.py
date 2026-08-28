from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import OAuthLoginUrlView, OAuthCallbackView, DevLoginView

urlpatterns = [
    path('oauth/', OAuthLoginUrlView.as_view(), name='oauth-url'),
    path('oauth/callback/', OAuthCallbackView.as_view(), name='oauth-callback'),
    path('dev-login/', DevLoginView.as_view(), name='dev-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
