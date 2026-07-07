from pathlib import Path

from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from .constants import ALLOWED_EXTENSIONS
from .models import (
    InstitutionalDocument,
    InstitutionalDocumentAccessLog,
    InstitutionalDocumentCategory,
    InstitutionalDocumentReview,
    InstitutionalDocumentTag,
    InstitutionalDocumentVersion,
)
from .services import create_new_version


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionalDocumentCategory
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"slug": {"required": False, "allow_blank": True}}


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionalDocumentTag
        fields = "__all__"


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionalDocumentVersion
        fields = "__all__"
        read_only_fields = ["file_name", "file_size", "mime_type", "checksum", "created_at", "uploaded_by"]


class DocumentReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionalDocumentReview
        fields = "__all__"
        read_only_fields = ["reviewed_at", "reviewer"]


class DocumentAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionalDocumentAccessLog
        fields = "__all__"
        read_only_fields = ["accessed_at"]


def validate_dates(attrs):
    effective_date = attrs.get("effective_date")
    review_date = attrs.get("review_date")
    expiry_date = attrs.get("expiry_date")
    if effective_date and review_date and review_date < effective_date:
        raise serializers.ValidationError({"review_date": ["Review date must not be before effective date."]})
    if effective_date and expiry_date and expiry_date < effective_date:
        raise serializers.ValidationError({"expiry_date": ["Expiry date must not be before effective date."]})


def validate_file_rules(document_type, file_obj, external_url):
    if document_type == "link":
        if not external_url:
            raise serializers.ValidationError({"external_url": ["External URL is required for link documents."]})
        return
    if not file_obj:
        raise serializers.ValidationError({"file": ["File is required unless document type is link."]})
    allowed_extensions = ALLOWED_EXTENSIONS.get(document_type, set())
    if allowed_extensions:
        extension = Path(file_obj.name).suffix.lower()
        if extension not in allowed_extensions:
            raise serializers.ValidationError({"file": [f"File extension must be one of: {', '.join(sorted(allowed_extensions))}."]})


class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False, allow_null=True)
    external_url = serializers.URLField(write_only=True, required=False, allow_blank=True)
    version_number = serializers.CharField(write_only=True, required=False, default="1.0")
    change_summary = serializers.CharField(write_only=True, required=False, allow_blank=True)
    tag_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    current_version_detail = VersionSerializer(source="current_version", read_only=True)
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = InstitutionalDocument
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "document_type",
            "description",
            "related_module",
            "visibility_level",
            "current_version",
            "current_version_detail",
            "status",
            "owner",
            "uploaded_by",
            "approved_by",
            "published_by",
            "approved_at",
            "published_at",
            "effective_date",
            "review_date",
            "expiry_date",
            "is_latest",
            "is_active",
            "tags",
            "tags_detail",
            "file",
            "external_url",
            "version_number",
            "change_summary",
            "tag_names",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "slug",
            "current_version",
            "status",
            "uploaded_by",
            "approved_by",
            "published_by",
            "approved_at",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        validate_dates(attrs)
        if self.instance is None:
            validate_file_rules(attrs.get("document_type"), attrs.get("file"), attrs.get("external_url", ""))
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        file_obj = validated_data.pop("file", None)
        external_url = validated_data.pop("external_url", "")
        version_number = validated_data.pop("version_number", "1.0")
        change_summary = validated_data.pop("change_summary", "")
        tag_names = validated_data.pop("tag_names", [])
        tags = validated_data.pop("tags", [])
        user = self.context["request"].user
        document = InstitutionalDocument.objects.create(uploaded_by=user, **validated_data)
        version = InstitutionalDocumentVersion.objects.create(
            document=document,
            version_number=version_number,
            file=file_obj,
            external_url=external_url,
            change_summary=change_summary,
            uploaded_by=user,
        )
        document.current_version = version
        document.save(update_fields=["current_version", "updated_at"])
        if tags:
            document.tags.set(tags)
        for tag_name in tag_names:
            tag, _ = InstitutionalDocumentTag.objects.get_or_create(name=tag_name, defaults={"slug": slugify(tag_name)})
            document.tags.add(tag)
        return document


class NewVersionSerializer(serializers.Serializer):
    file = serializers.FileField(required=False, allow_null=True)
    external_url = serializers.URLField(required=False, allow_blank=True)
    version_number = serializers.CharField()
    change_summary = serializers.CharField(required=False, allow_blank=True)
    submit_for_review = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        document = self.context["document"]
        validate_file_rules(document.document_type, attrs.get("file"), attrs.get("external_url", ""))
        if document.versions.filter(version_number=attrs["version_number"]).exists():
            raise serializers.ValidationError({"version_number": ["Version number must be unique per document."]})
        return attrs

    def save(self, **kwargs):
        document = self.context["document"]
        user = self.context["request"].user
        return create_new_version(
            document=document,
            uploaded_by=user,
            version_number=self.validated_data["version_number"],
            file=self.validated_data.get("file"),
            external_url=self.validated_data.get("external_url", ""),
            change_summary=self.validated_data.get("change_summary", ""),
            submit=self.validated_data.get("submit_for_review", False),
        )


class ReviewActionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)
