from rest_framework.permissions import SAFE_METHODS, BasePermission


MANAGER_ROLES = {"admin", "principle_officer", "focal_person"}
DELETE_ROLES = {"admin", "principle_officer"}


def role_for(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if user.is_superuser or user.is_staff:
        return "admin"
    profile = getattr(user, "profile", None)
    return getattr(profile, "status", None)


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
        if request.method in SAFE_METHODS:
            return obj.submitted_by_id == request.user.id
        return False
