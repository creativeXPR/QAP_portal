from rest_framework import viewsets, permissions
from .models import Update
from .serializers import UpdateSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit or create.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Check if user is staff or has admin profile
        is_staff = request.user and request.user.is_staff
        has_admin_profile = False
        if request.user and hasattr(request.user, 'profile'):
            has_admin_profile = request.user.profile.status == 'admin'
        return bool(is_staff or has_admin_profile)

class UpdateViewSet(viewsets.ModelViewSet):
    serializer_class = UpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        
        # If the user is an admin, they can probably see all updates (optional, but good practice)
        if user.is_staff or (hasattr(user, 'profile') and user.profile.status == 'admin'):
            return Update.objects.all()
            
        # Filter updates based on the authenticated user's status
        if hasattr(user, 'profile'):
            return Update.objects.filter(forUser=user.profile.status)
            
        # Fallback if the user has no profile
        return Update.objects.none()
