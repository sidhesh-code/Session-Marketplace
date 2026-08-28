import requests
from django.conf import settings
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from accounts.serializers import UserSerializer, ProfileUpdateSerializer, DevLoginSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # Include custom claims if needed
    refresh['role'] = user.role
    refresh['email'] = user.email
    refresh['name'] = user.name
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    }

class OAuthLoginUrlView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        client_id = settings.GOOGLE_CLIENT_ID
        redirect_uri = settings.GOOGLE_REDIRECT_URI

        if not client_id or "your-google-client-id" in client_id:
            return Response(
                {
                    "detail": "Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env, or use Quick Login."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code&client_id={client_id}&"
            f"redirect_uri={redirect_uri}&scope={scope}"
        )
        return Response({"auth_url": auth_url})

class OAuthCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code')
        role = request.data.get('role', User.Role.USER)
        
        if not code:
            return Response({"detail": "Authorization code is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Exchange authorization code for Google access token
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        try:
            token_response = requests.post(token_url, data=payload, timeout=10)
            if token_response.status_code != 200:
                return Response({
                    "detail": "Failed to exchange Google OAuth code.",
                    "error": token_response.json()
                }, status=status.HTTP_400_BAD_REQUEST)
                
            google_access_token = token_response.json().get('access_token')
            
            # Fetch user info from Google
            user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            user_info_resp = requests.get(
                user_info_url,
                headers={"Authorization": f"Bearer {google_access_token}"},
                timeout=10
            )
            
            if user_info_resp.status_code != 200:
                return Response({"detail": "Failed to retrieve user info from Google."}, status=status.HTTP_400_BAD_REQUEST)
                
            google_data = user_info_resp.json()
            email = google_data.get('email')
            name = google_data.get('name', email.split('@')[0])
            picture = google_data.get('picture')

            if not email:
                return Response({"detail": "Google profile missing email address."}, status=status.HTTP_400_BAD_REQUEST)

            # Get or create User in local database
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'role': role if role in User.Role.values else User.Role.USER,
                    'profile_image': picture
                }
            )

            # Issue JWT access & refresh tokens
            tokens = get_tokens_for_user(user)
            return Response(tokens, status=status.HTTP_200_OK)

        except requests.RequestException as e:
            return Response({"detail": f"Network error connecting to Google OAuth: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DevLoginView(APIView):
    """
    Developer / Testing authentication endpoint to issue JWT tokens instantly for UI testing and automated evaluation.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = DevLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        name = serializer.validated_data.get('name', email.split('@')[0])
        role = serializer.validated_data.get('role', User.Role.USER)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'role': role
            }
        )
        if not created and user.role != role:
            user.role = role
            user.save(update_fields=['role'])

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
