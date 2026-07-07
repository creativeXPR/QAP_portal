from django.contrib import admin

from .models import (
    CommitteeMeeting,
    CommitteeMeetingAttendance,
    QAActionEvidence,
    QAActionPlan,
    QAAuditCycle,
    QAAuditFinding,
    QACommittee,
    QACommitteeDataReview,
    QACommitteeMember,
    QACommitteeReport,
    QARecommendation,
)


@admin.register(QACommittee)
class QACommitteeAdmin(admin.ModelAdmin):
    list_display = ("name", "scope_type", "faculty", "department", "programme", "status", "date_constituted")
    list_filter = ("scope_type", "status", "faculty", "department")
    search_fields = ("name", "description", "programme")


@admin.register(QACommitteeMember)
class QACommitteeMemberAdmin(admin.ModelAdmin):
    list_display = ("committee", "user", "role", "designation", "is_active")
    list_filter = ("role", "is_active", "committee")
    search_fields = ("committee__name", "user__username", "user__email", "designation")


@admin.register(CommitteeMeeting)
class CommitteeMeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "committee", "meeting_type", "scheduled_date", "held_date", "status")
    list_filter = ("meeting_type", "status", "committee")
    search_fields = ("title", "agenda", "minutes", "committee__name")


@admin.register(CommitteeMeetingAttendance)
class CommitteeMeetingAttendanceAdmin(admin.ModelAdmin):
    list_display = ("meeting", "member", "attendance_status")
    list_filter = ("attendance_status", "meeting")


@admin.register(QAAuditCycle)
class QAAuditCycleAdmin(admin.ModelAdmin):
    list_display = ("title", "committee", "audit_type", "review_period_start", "review_period_end", "status")
    list_filter = ("audit_type", "status", "committee", "target_faculty", "target_department")
    search_fields = ("title", "target_programme")


@admin.register(QAAuditFinding)
class QAAuditFindingAdmin(admin.ModelAdmin):
    list_display = ("finding_code", "title", "audit_cycle", "source_module", "severity", "risk_level", "status")
    list_filter = ("source_module", "category", "severity", "risk_level", "status")
    search_fields = ("finding_code", "title", "description", "source_record_type", "source_record_id")


@admin.register(QARecommendation)
class QARecommendationAdmin(admin.ModelAdmin):
    list_display = ("title", "audit_cycle", "priority", "status", "due_date", "assigned_to")
    list_filter = ("priority", "status", "responsible_unit_type", "responsible_faculty", "responsible_department")
    search_fields = ("title", "recommendation_text")


@admin.register(QAActionPlan)
class QAActionPlanAdmin(admin.ModelAdmin):
    list_display = ("recommendation", "owner", "expected_completion_date", "progress_percentage", "status")
    list_filter = ("status", "expected_completion_date")
    search_fields = ("action_description", "implementation_notes", "recommendation__title")


@admin.register(QAActionEvidence)
class QAActionEvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "action_plan", "verification_status", "uploaded_by", "verified_by")
    list_filter = ("verification_status",)
    search_fields = ("title", "description", "external_url")


@admin.register(QACommitteeReport)
class QACommitteeReportAdmin(admin.ModelAdmin):
    list_display = ("committee", "report_type", "reporting_period_start", "reporting_period_end", "status", "qacei_score")
    list_filter = ("report_type", "status", "committee")
    search_fields = ("summary", "key_findings", "recommendations_summary")


@admin.register(QACommitteeDataReview)
class QACommitteeDataReviewAdmin(admin.ModelAdmin):
    list_display = ("review_title", "committee", "source_module", "validation_status", "reviewer")
    list_filter = ("source_module", "validation_status", "committee")
    search_fields = ("review_title", "source_endpoint_or_model", "reviewer_comment")
