from django.urls import path
from sessions_app.views import CreatorSessionListView, CreatorSessionDetailView

urlpatterns = [
    path('', CreatorSessionListView.as_view(), name='creator-session-list'),
    path('<int:pk>/', CreatorSessionDetailView.as_view(), name='creator-session-detail'),
]
