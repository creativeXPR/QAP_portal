from pathlib import Path

from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpResponseRedirect
from django.utils import timezone

from .constants import DEFAULT_CATEGORIES
from .models import (
    InstitutionalDocument,
    InstitutionalDocumentAccessLog,
    InstitutionalDocumentCategory,
    InstitutionalDocumentReview,
    InstitutionalDocumentVersion,
)


def ensure_default_categories():
    for name, slug, description in DEFAULT_CATEGORIES:
        InstitutionalDocumentCategory.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "description": description, "is_active": True},
        )


def has_version_payload(document):
    version = document.current_version
    if not version:
        return False
    if document.document_type == "link":
        return bool(version.external_url)
    return bool(version.file)


def submit_for_review(document):
    if not has_version_payload(document):
        raise ValidationError("Cannot submit for review without a file or link.")
    document.status = "pending_review"
    if document.current_version:
        document.current_version.status = "pending_review"
        document.current_version.save(update_fields=["status"])
    document.save(update_fields=["status", "updated_at"])
    return document


def approve_document(document, reviewer, comment=""):
    if not document.current_version:
        raise ValidationError("Cannot approve document without at least one version.")
    document.status = "approved"
    document.approved_by = reviewer
    document.approved_at = timezone.now()
    document.current_version.status = "approved"
    document.current_version.save(update_fields=["status"])
    document.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    InstitutionalDocumentReview.objects.create(
        document=document,
        version=document.current_version,
        reviewer=reviewer,
        decision="approved",
        comment=comment,
    )
    return document


def reject_document(document, reviewer, comment=""):
    if not document.current_version:
        raise ValidationError("Cannot reject document without at least one version.")
    document.status = "rejected"
    document.current_version.status = "rejected"
    document.current_version.save(update_fields=["status"])
    document.save(update_fields=["status", "updated_at"])
    InstitutionalDocumentReview.objects.create(
        document=document,
        version=document.current_version,
        reviewer=reviewer,
        decision="rejected",
        comment=comment,
    )
    return document


def publish_document(document, publisher):
    if document.status != "approved":
        raise ValidationError("Only approved documents can be published.")
    if not document.current_version:
        raise ValidationError("Cannot publish document without at least one version.")
    document.status = "published"
    document.published_by = publisher
    document.published_at = timezone.now()
    document.is_latest = True
    document.is_active = True
    document.current_version.status = "published"
    document.current_version.save(update_fields=["status"])
    document.versions.exclude(pk=document.current_version_id).filter(status="published").update(status="archived")
    document.save(update_fields=["status", "published_by", "published_at", "is_latest", "is_active", "updated_at"])
    return document


def archive_document(document):
    document.status = "archived"
    document.is_active = False
    document.save(update_fields=["status", "is_active", "updated_at"])
    return document


def create_new_version(document, uploaded_by, version_number, file=None, external_url="", change_summary="", submit=False):
    version = InstitutionalDocumentVersion.objects.create(
        document=document,
        version_number=version_number,
        file=file,
        external_url=external_url,
        change_summary=change_summary,
        uploaded_by=uploaded_by,
        status="pending_review" if submit else "draft",
    )
    document.current_version = version
    document.status = "pending_review" if submit else "draft"
    document.approved_by = None
    document.approved_at = None
    document.published_by = None
    document.published_at = None
    document.save()
    return version


def client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_access(request, document, action):
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    return InstitutionalDocumentAccessLog.objects.create(
        document=document,
        version=document.current_version,
        user=user,
        action=action,
        ip_address=client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def access_response(request, document, action):
    version = document.current_version
    if not version:
        raise ValidationError("Document has no available version.")
    log_access(request, document, action)
    if document.document_type == "link":
        if not version.external_url:
            raise ValidationError("Document link is missing.")
        return HttpResponseRedirect(version.external_url)
    if not version.file:
        raise ValidationError("Document file is missing.")
    as_attachment = action == "downloaded"
    filename = version.file_name or Path(version.file.name).name
    return FileResponse(version.file.open("rb"), as_attachment=as_attachment, filename=filename)
