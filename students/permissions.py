from rest_framework.permissions import SAFE_METHODS, BasePermission

from authentication.roles import DELETE_ROLES, MANAGER_ROLES, role_for


class StudentRecordPermission(BasePermission):
    def has_permission(self, request, view):
        if not getattr(request.user, "is_authenticated", False):
            return False
        role = role_for(request.user)
        if request.method == "DELETE":
            return role in DELETE_ROLES
        if request.method in SAFE_METHODS:
            return True
        return role in MANAGER_ROLES

    def has_object_permission(self, request, view, obj):
        role = role_for(request.user)
        if request.method == "DELETE":
            return role in DELETE_ROLES
        if request.method in SAFE_METHODS:
            return role in MANAGER_ROLES or obj.user_id == request.user.id
        return role in MANAGER_ROLES


class StudentFeedbackPermission(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, "is_authenticated", False)

    def has_object_permission(self, request, view, obj):
        role = role_for(request.user)
        if role in MANAGER_ROLES:
            return True
        owner_id = getattr(obj, "submitted_by_id", None) or getattr(obj, "user_id", None)
        if request.method in SAFE_METHODS:
            return owner_id == request.user.id
        return owner_id == request.user.id and getattr(view, "action", None) == "mark_read"
