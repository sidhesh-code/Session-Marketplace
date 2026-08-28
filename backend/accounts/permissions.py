from rest_framework.permissions import BasePermission
from accounts.models import User

class IsCreator(BasePermission):
    """
    Allows access only to authenticated users with the CREATOR role.
    """
    message = "Only creators can perform this action."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.CREATOR
        )

class IsUserRole(BasePermission):
    """
    Allows access only to authenticated users with the USER role (for booking, viewing bookings).
    """
    message = "Only regular users can perform booking actions."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == User.Role.USER
        )

class IsSessionOwner(BasePermission):
    """
    Allows access only to the Creator who owns the session.
    """
    message = "You are not authorized to modify or delete another creator's session."

    def has_object_permission(self, request, view, obj):
        return (
            request.user and
            request.user.is_authenticated and
            obj.creator == request.user
        )
