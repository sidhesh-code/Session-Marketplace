from django.urls import path
from bookings.views import (
    BookSessionView, BookingListView, ActiveBookingListView, 
    PastBookingListView, CancelBookingView
)

urlpatterns = [
    path('', BookingListView.as_view(), name='booking-list'),
    path('active/', ActiveBookingListView.as_view(), name='booking-list-active'),
    path('past/', PastBookingListView.as_view(), name='booking-list-past'),
    path('<int:pk>/cancel/', CancelBookingView.as_view(), name='booking-cancel'),
]
