from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "service": "sessions-marketplace-backend"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/auth/', include('accounts.urls_auth')),
    path('api/profile/', include('accounts.urls_profile')),
    path('api/sessions/', include('sessions_app.urls_public')),
    path('api/creator/sessions/', include('sessions_app.urls_creator')),
    path('api/bookings/', include('bookings.urls')),
]
