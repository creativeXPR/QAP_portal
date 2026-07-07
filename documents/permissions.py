from rest_framework.permissions import SAFE_METHODS, BasePermission


DQA_ADMIN_ROLES = {"admin"}
REVIEWER_ROLES = {"admin", "principle_officer"}
PUBLISHER_ROLES = {"admin", "principle_officer"}
UPLOADER_ROLES = {"admin", "principle_officer", "focal_person"}


def role_for(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if user.is_superuser or user.is_staff:
        return "admin"
    profile = getattr(user, "profile", None)
    return getattr(profile, "status", None)


def can_upload(user):
    return role_for(user) in UPLOADER_ROLES


def can_review(user):
    return role_for(user) in REVIEWER_ROLES


def can_publish(user):
    return role_for(user) in PUBLISHER_ROLES


def can_admin(user):
    return role_for(user) in DQA_ADMIN_ROLES


def can_view_document(user, document):
    role = role_for(user)
    if role in REVIEWER_ROLES:
        return True
    if document.status in {"draft", "rejected"}:
        return getattr(user, "is_authenticated", False) and document.uploaded_by_id == user.id
    if document.status == "archived":
        return role in REVIEWER_ROLES
    if document.visibility_level == "public":
        return document.status == "published"
    if not getattr(user, "is_authenticated", False):
        return False
    if document.visibility_level == "all_authenticated":
        return document.status == "published"
    if document.visibility_level == "qa_focal_persons":
        return role in {"focal_person", "admin", "principle_officer"} and document.status == "published"
    if document.visibility_level == "hods_and_deans":
        return role in {"principle_officer", "admin"} and document.status == "published"
    if document.visibility_level == "committee_members":
        return role in {"principle_officer", "admin"} and document.status == "published"
    if document.visibility_level == "dqa_only":
        return role in REVIEWER_ROLES and document.status == "published"
    if document.visibility_level == "private":
        return document.uploaded_by_id == user.id
    return False


class InstitutionalDocumentPermission(BasePermission):
    def has_permission(self, request, view):
        action = getattr(view, "action", None)
        if request.method in SAFE_METHODS or action in {"preview", "download"}:
            return True
        if action in {"approve", "reject"}:
            return can_review(request.user)
        if action == "publish":
            return can_publish(request.user)
        if action in {"create", "update", "partial_update", "destroy", "new_version", "submit_for_review", "archive"}:
            return can_upload(request.user)
        return getattr(request.user, "is_authenticated", False)

    def has_object_permission(self, request, view, obj):
        action = getattr(view, "action", None)
        if request.method in SAFE_METHODS or action in {"preview", "download"}:
            return can_view_document(request.user, obj) if hasattr(obj, "visibility_level") else True
        if action in {"approve", "reject"}:
            return can_review(request.user)
        if action == "publish":
            return can_publish(request.user)
        if can_admin(request.user):
            return True
        return getattr(obj, "uploaded_by_id", None) == getattr(request.user, "id", None)
