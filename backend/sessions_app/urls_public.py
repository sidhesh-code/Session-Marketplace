from django.urls import path
from sessions_app.views import PublicSessionListView, PublicSessionDetailView
from bookings.views import BookSessionView

urlpatterns = [
    path('', PublicSessionListView.as_view(), name='public-session-list'),
    path('<int:pk>/', PublicSessionDetailView.as_view(), name='public-session-detail'),
    path('<int:session_id>/book/', BookSessionView.as_view(), name='public-session-book'),
]
