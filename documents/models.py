import hashlib

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .constants import (
    ACCESS_ACTIONS,
    DOCUMENT_STATUSES,
    DOCUMENT_TYPES,
    RELATED_MODULES,
    REVIEW_DECISIONS,
    VISIBILITY_LEVELS,
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class InstitutionalDocumentCategory(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class InstitutionalDocumentTag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class InstitutionalDocument(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    category = models.ForeignKey(InstitutionalDocumentCategory, related_name="documents", on_delete=models.PROTECT)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    description = models.TextField(blank=True)
    related_module = models.CharField(max_length=40, choices=RELATED_MODULES)
    visibility_level = models.CharField(max_length=40, choices=VISIBILITY_LEVELS)
    current_version = models.ForeignKey(
        "InstitutionalDocumentVersion",
        null=True,
        blank=True,
        related_name="current_for_documents",
        on_delete=models.SET_NULL,
    )
    status = models.CharField(max_length=30, choices=DOCUMENT_STATUSES, default="draft")
    owner = models.CharField(max_length=160, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="uploaded_documents", on_delete=models.SET_NULL)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="approved_documents", on_delete=models.SET_NULL)
    published_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name="published_documents", on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_latest = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    tags = models.ManyToManyField(InstitutionalDocumentTag, blank=True, related_name="documents")

    class Meta:
        ordering = ["-created_at", "title"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
            models.Index(fields=["related_module"]),
            models.Index(fields=["visibility_level"]),
            models.Index(fields=["document_type"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 2
            while InstitutionalDocument.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class InstitutionalDocumentVersion(models.Model):
    document = models.ForeignKey(InstitutionalDocument, related_name="versions", on_delete=models.CASCADE)
    version_number = models.CharField(max_length=30)
    file = models.FileField(upload_to="institutional_documents/", null=True, blank=True)
    external_url = models.URLField(blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=120, blank=True)
    checksum = models.CharField(max_length=64, blank=True)
    change_summary = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=30, choices=DOCUMENT_STATUSES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["document", "version_number"], name="unique_document_version_number"),
        ]

    def save(self, *args, **kwargs):
        if self.file:
            self.file_name = self.file.name.split("/")[-1]
            self.file_size = self.file.size
            content_type = getattr(self.file.file, "content_type", "") or getattr(self.file, "content_type", "")
            if content_type:
                self.mime_type = content_type
            if not self.checksum:
                position = self.file.tell() if hasattr(self.file, "tell") else None
                self.file.seek(0)
                digest = hashlib.sha256()
                for chunk in self.file.chunks():
                    digest.update(chunk)
                self.checksum = digest.hexdigest()
                self.file.seek(position or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.document.title} v{self.version_number}"


class InstitutionalDocumentReview(models.Model):
    document = models.ForeignKey(InstitutionalDocument, related_name="reviews", on_delete=models.CASCADE)
    version = models.ForeignKey(InstitutionalDocumentVersion, related_name="reviews", on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    decision = models.CharField(max_length=30, choices=REVIEW_DECISIONS)
    comment = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-reviewed_at"]

    def __str__(self):
        return f"{self.document.title}: {self.decision}"


class InstitutionalDocumentAccessLog(models.Model):
    document = models.ForeignKey(InstitutionalDocument, related_name="access_logs", on_delete=models.CASCADE)
    version = models.ForeignKey(InstitutionalDocumentVersion, null=True, blank=True, related_name="access_logs", on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20, choices=ACCESS_ACTIONS)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    accessed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-accessed_at"]
        indexes = [
            models.Index(fields=["document", "action"]),
            models.Index(fields=["accessed_at"]),
        ]

    def __str__(self):
        return f"{self.document.title}: {self.action}"
