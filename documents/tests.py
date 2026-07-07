import shutil
import tempfile
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import (
    InstitutionalDocument,
    InstitutionalDocumentAccessLog,
    InstitutionalDocumentCategory,
    InstitutionalDocumentVersion,
)
from .services import ensure_default_categories


MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class InstitutionalDocumentsApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            username="dqa_admin",
            email="dqa_admin@example.com",
            password="password",
        )
        self.viewer = get_user_model().objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="password",
        )
        self.client.force_authenticate(self.admin)
        ensure_default_categories()
        self.category = InstitutionalDocumentCategory.objects.get(slug="policy-documents")

    def pdf_file(self, name="policy.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1.4 test file", content_type="application/pdf")

    def create_file_document(self, title="Quality Assurance Policy", visibility="all_authenticated"):
        response = self.client.post(
            "/api/institutional-documents/documents/",
            {
                "title": title,
                "category": self.category.id,
                "document_type": "pdf",
                "related_module": "institutional_policy",
                "visibility_level": visibility,
                "description": "Official QA policy.",
                "effective_date": str(date.today()),
                "review_date": str(date.today() + timedelta(days=365)),
                "file": self.pdf_file(),
                "change_summary": "Initial upload",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return InstitutionalDocument.objects.get(pk=response.data["data"]["id"])

    def publish_document(self, document):
        self.client.post(f"/api/institutional-documents/documents/{document.id}/submit-for-review/")
        self.client.post(
            f"/api/institutional-documents/documents/{document.id}/approve/",
            {"comment": "Approved."},
            format="json",
        )
        response = self.client.post(f"/api/institutional-documents/documents/{document.id}/publish/")
        self.assertEqual(response.status_code, 200, response.data)
        document.refresh_from_db()
        return document

    def test_category_creation_and_soft_delete(self):
        response = self.client.post(
            "/api/institutional-documents/categories/",
            {"name": "Board Papers", "slug": "board-papers", "description": "Council and board papers."},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        category_id = response.data["data"]["id"]
        response = self.client.delete(f"/api/institutional-documents/categories/{category_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(InstitutionalDocumentCategory.objects.get(pk=category_id).is_active)

    def test_document_creation_with_file_and_link(self):
        document = self.create_file_document()
        self.assertEqual(document.versions.count(), 1)
        self.assertEqual(document.current_version.version_number, "1.0")
        self.assertTrue(document.current_version.file_name.endswith(".pdf"))

        response = self.client.post(
            "/api/institutional-documents/documents/",
            {
                "title": "QA Orientation Slides",
                "category": self.category.id,
                "document_type": "link",
                "related_module": "qa_committee",
                "visibility_level": "qa_focal_persons",
                "description": "Orientation debriefing slides.",
                "external_url": "https://example.com/slides",
                "change_summary": "Initial link upload",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        link_document = InstitutionalDocument.objects.get(pk=response.data["data"]["id"])
        self.assertEqual(link_document.current_version.external_url, "https://example.com/slides")

    def test_validation_failures_for_missing_file_or_link_and_bad_dates(self):
        response = self.client.post(
            "/api/institutional-documents/documents/",
            {
                "title": "Missing File",
                "category": self.category.id,
                "document_type": "pdf",
                "related_module": "institutional_policy",
                "visibility_level": "all_authenticated",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data["errors"])

        response = self.client.post(
            "/api/institutional-documents/documents/",
            {
                "title": "Missing Link",
                "category": self.category.id,
                "document_type": "link",
                "related_module": "platform_documentation",
                "visibility_level": "public",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("external_url", response.data["errors"])

        response = self.client.post(
            "/api/institutional-documents/documents/",
            {
                "title": "Bad Date",
                "category": self.category.id,
                "document_type": "pdf",
                "related_module": "institutional_policy",
                "visibility_level": "all_authenticated",
                "effective_date": "2026-07-10",
                "review_date": "2026-07-01",
                "file": self.pdf_file("bad-date.pdf"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("review_date", response.data["errors"])

    def test_submit_approve_reject_publish_and_archive_workflow(self):
        document = self.create_file_document()
        publish_response = self.client.post(f"/api/institutional-documents/documents/{document.id}/publish/")
        self.assertEqual(publish_response.status_code, 400)

        response = self.client.post(f"/api/institutional-documents/documents/{document.id}/submit-for-review/")
        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.status, "pending_review")

        response = self.client.post(
            f"/api/institutional-documents/documents/{document.id}/reject/",
            {"comment": "Fix review date."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.status, "rejected")

        self.client.post(f"/api/institutional-documents/documents/{document.id}/submit-for-review/")
        response = self.client.post(
            f"/api/institutional-documents/documents/{document.id}/approve/",
            {"comment": "Ready."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.status, "approved")

        response = self.client.post(f"/api/institutional-documents/documents/{document.id}/publish/")
        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.status, "published")

        response = self.client.post(f"/api/institutional-documents/documents/{document.id}/archive/")
        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.status, "archived")
        self.assertFalse(document.is_active)

    def test_normal_user_cannot_approve_or_publish_documents(self):
        document = self.create_file_document()
        self.client.post(f"/api/institutional-documents/documents/{document.id}/submit-for-review/")
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            f"/api/institutional-documents/documents/{document.id}/approve/",
            {"comment": "Trying to approve."},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(f"/api/institutional-documents/documents/{document.id}/publish/")
        self.assertEqual(response.status_code, 403)

    def test_upload_new_version_keeps_old_version_available(self):
        document = self.publish_document(self.create_file_document())
        old_version = document.current_version
        response = self.client.post(
            f"/api/institutional-documents/documents/{document.id}/new-version/",
            {
                "version_number": "1.1",
                "file": self.pdf_file("policy-1-1.pdf"),
                "change_summary": "Updated policy section.",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        document.refresh_from_db()
        self.assertEqual(document.current_version.version_number, "1.1")
        self.assertTrue(InstitutionalDocumentVersion.objects.filter(pk=old_version.pk).exists())
        self.assertEqual(document.versions.count(), 2)

    def test_download_and_preview_create_access_logs(self):
        document = self.publish_document(self.create_file_document())
        self.client.force_authenticate(self.viewer)
        response = self.client.get(f"/api/institutional-documents/documents/{document.id}/preview/")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(f"/api/institutional-documents/documents/{document.id}/download/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(InstitutionalDocumentAccessLog.objects.filter(document=document).count(), 2)

    def test_visibility_permission_rules(self):
        private_document = self.publish_document(self.create_file_document(title="Private Policy", visibility="private"))
        public_document = self.publish_document(self.create_file_document(title="Public Policy", visibility="public"))

        self.client.force_authenticate(self.viewer)
        response = self.client.get(f"/api/institutional-documents/documents/{private_document.id}/")
        self.assertEqual(response.status_code, 404)

        anonymous = APIClient()
        response = anonymous.get(f"/api/institutional-documents/documents/{public_document.id}/")
        self.assertEqual(response.status_code, 200)

    def test_filtering_and_search(self):
        policy = self.publish_document(self.create_file_document(title="Quality Policy"))
        manual_category = InstitutionalDocumentCategory.objects.get(slug="user-manuals")
        response = self.client.post(
            "/api/institutional-documents/documents/",
            {
                "title": "Portal Manual",
                "category": manual_category.id,
                "document_type": "pdf",
                "related_module": "platform_documentation",
                "visibility_level": "all_authenticated",
                "file": self.pdf_file("manual.pdf"),
                "tag_names": ["manual"],
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)

        response = self.client.get("/api/institutional-documents/documents/", {"search": "quality"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["id"] == policy.id for item in response.data["data"]))

        response = self.client.get(
            "/api/institutional-documents/documents/",
            {"category": manual_category.id, "document_type": "pdf", "search": "manual"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
