from rest_framework.permissions import BasePermission, SAFE_METHODS

class KPIPermission(BasePermission):
    """
    Custom permission for KPI model:
    - Safe methods (GET, HEAD, OPTIONS): Accessed only by status in ('admin', 'principle_officer') or superuser.
    - Write methods (POST, PUT, PATCH, DELETE): Accessed only by status == 'admin' or superuser.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
            
        if request.user.is_superuser:
            return True
            
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return False
            
        # Write operations (POST, PUT, PATCH, DELETE)
        if request.method not in SAFE_METHODS:
            return profile.status == 'admin'
            
        # Read operations (GET, etc.)
        return profile.status in ('admin', 'principle_officer')