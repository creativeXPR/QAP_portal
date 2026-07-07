from django.contrib import admin

from .models import (
    InstitutionalDocument,
    InstitutionalDocumentAccessLog,
    InstitutionalDocumentCategory,
    InstitutionalDocumentReview,
    InstitutionalDocumentTag,
    InstitutionalDocumentVersion,
)


admin.site.register(InstitutionalDocumentCategory)
admin.site.register(InstitutionalDocumentTag)
admin.site.register(InstitutionalDocument)
admin.site.register(InstitutionalDocumentVersion)
admin.site.register(InstitutionalDocumentReview)
admin.site.register(InstitutionalDocumentAccessLog)
