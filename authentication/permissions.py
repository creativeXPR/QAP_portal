from rest_framework.permissions import BasePermission

from .roles import role_for

class IsAdminUserStatus(BasePermission):
    """
    Allows access only to authenticated users who have 'admin' status in their Profile.
    Superusers are also permitted.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Superusers bypass the status check
        if request.user.is_superuser:
            return True
            
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.status == 'admin'