from django.db import models
from django.conf import settings

class Booking(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        CANCELLED = 'CANCELLED', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    session = models.ForeignKey(
        'sessions_app.Session',
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'session'],
                condition=models.Q(status='ACTIVE'),
                name='unique_active_booking_per_user_session'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking #{self.id} by {self.user.name} for {self.session.title} [{self.status}]"
