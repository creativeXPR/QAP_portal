from django.utils import timezone
from rest_framework import serializers

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


class QACommitteeSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(source="faculty.name", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = QACommittee
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at", "faculty_name", "department_name", "created_by_username"]

    def validate(self, attrs):
        scope_type = attrs.get("scope_type", getattr(self.instance, "scope_type", None))
        faculty = attrs.get("faculty", getattr(self.instance, "faculty", None))
        department = attrs.get("department", getattr(self.instance, "department", None))
        programme = attrs.get("programme", getattr(self.instance, "programme", ""))
        status = attrs.get("status", getattr(self.instance, "status", QACommittee.Status.ACTIVE))
        if scope_type == QACommittee.ScopeType.DEPARTMENT and not department:
            raise serializers.ValidationError({"department": ["Department-level committee requires a department."]})
        if scope_type == QACommittee.ScopeType.FACULTY and not faculty:
            raise serializers.ValidationError({"faculty": ["Faculty-level committee requires a faculty."]})
        if scope_type == QACommittee.ScopeType.PROGRAMME and not programme:
            raise serializers.ValidationError({"programme": ["Programme-level committee requires a programme."]})
        if faculty and department and department.faculty_id != faculty.id:
            raise serializers.ValidationError({"department": ["Department must belong to the selected faculty."]})
        if status == QACommittee.Status.ACTIVE:
            duplicate = QACommittee.objects.filter(
                scope_type=scope_type,
                faculty=faculty,
                department=department,
                programme=programme,
                status=QACommittee.Status.ACTIVE,
            ).exclude(pk=getattr(self.instance, "pk", None))
            if duplicate.exists():
                raise serializers.ValidationError({"scope_type": ["An active committee already exists for this scope."]})
        return attrs


class QACommitteeMemberSerializer(serializers.ModelSerializer):
    committee_name = serializers.CharField(source="committee.name", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = QACommitteeMember
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "committee_name", "user_name", "user_email"]

    def validate(self, attrs):
        committee = attrs.get("committee", getattr(self.instance, "committee", None))
        role = attrs.get("role", getattr(self.instance, "role", None))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": ["End date cannot be before start date."]})
        if committee and is_active and role in {QACommitteeMember.Role.CHAIRPERSON, QACommitteeMember.Role.SECRETARY}:
            duplicate = QACommitteeMember.objects.filter(committee=committee, role=role, is_active=True).exclude(pk=getattr(self.instance, "pk", None))
            if duplicate.exists():
                raise serializers.ValidationError({"role": [f"Only one active {role} is allowed per committee."]})
        return attrs


class CommitteeMeetingAttendanceSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source="member.user.get_full_name", read_only=True)

    class Meta:
        model = CommitteeMeetingAttendance
        fields = "__all__"
        read_only_fields = ["member_name"]


class CommitteeMeetingSerializer(serializers.ModelSerializer):
    committee_name = serializers.CharField(source="committee.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    attendance = CommitteeMeetingAttendanceSerializer(many=True, read_only=True)

    class Meta:
        model = CommitteeMeeting
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at", "committee_name", "created_by_username", "attendance"]


class QAAuditCycleSerializer(serializers.ModelSerializer):
    committee_name = serializers.CharField(source="committee.name", read_only=True)
    target_faculty_name = serializers.CharField(source="target_faculty.name", read_only=True)
    target_department_name = serializers.CharField(source="target_department.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = QAAuditCycle
        fields = "__all__"
        read_only_fields = [
            "created_by",
            "created_at",
            "updated_at",
            "committee_name",
            "target_faculty_name",
            "target_department_name",
            "created_by_username",
        ]


class QAAuditFindingSerializer(serializers.ModelSerializer):
    audit_cycle_title = serializers.CharField(source="audit_cycle.title", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = QAAuditFinding
        fields = "__all__"
        read_only_fields = ["finding_code", "created_by", "created_at", "updated_at", "audit_cycle_title", "created_by_username"]


class QARecommendationSerializer(serializers.ModelSerializer):
    finding_title = serializers.CharField(source="finding.title", read_only=True)
    audit_cycle_title = serializers.CharField(source="audit_cycle.title", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    responsible_faculty_name = serializers.CharField(source="responsible_faculty.name", read_only=True)
    responsible_department_name = serializers.CharField(source="responsible_department.name", read_only=True)

    class Meta:
        model = QARecommendation
        fields = "__all__"
        read_only_fields = [
            "created_by",
            "created_at",
            "updated_at",
            "finding_title",
            "audit_cycle_title",
            "assigned_to_username",
            "responsible_faculty_name",
            "responsible_department_name",
        ]


class QAActionPlanSerializer(serializers.ModelSerializer):
    recommendation_title = serializers.CharField(source="recommendation.title", read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = QAActionPlan
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at", "recommendation_title", "owner_username"]


class QAActionEvidenceSerializer(serializers.ModelSerializer):
    action_plan_description = serializers.CharField(source="action_plan.action_description", read_only=True)
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)
    verified_by_username = serializers.CharField(source="verified_by.username", read_only=True)

    class Meta:
        model = QAActionEvidence
        fields = "__all__"
        read_only_fields = [
            "uploaded_by",
            "verified_by",
            "created_at",
            "updated_at",
            "action_plan_description",
            "uploaded_by_username",
            "verified_by_username",
        ]

    def validate(self, attrs):
        file_obj = attrs.get("file", getattr(self.instance, "file", None))
        external_url = attrs.get("external_url", getattr(self.instance, "external_url", ""))
        if not file_obj and not external_url:
            raise serializers.ValidationError({"external_url": ["Either file or external_url must be provided."]})
        return attrs


class QACommitteeReportSerializer(serializers.ModelSerializer):
    committee_name = serializers.CharField(source="committee.name", read_only=True)
    audit_cycle_title = serializers.CharField(source="audit_cycle.title", read_only=True)
    submitted_by_username = serializers.CharField(source="submitted_by.username", read_only=True)
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True)

    class Meta:
        model = QACommitteeReport
        fields = "__all__"
        read_only_fields = [
            "submitted_by",
            "submitted_at",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
            "committee_name",
            "audit_cycle_title",
            "submitted_by_username",
            "reviewed_by_username",
        ]


class QACommitteeDataReviewSerializer(serializers.ModelSerializer):
    committee_name = serializers.CharField(source="committee.name", read_only=True)
    target_faculty_name = serializers.CharField(source="target_faculty.name", read_only=True)
    target_department_name = serializers.CharField(source="target_department.name", read_only=True)
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True)

    class Meta:
        model = QACommitteeDataReview
        fields = "__all__"
        read_only_fields = [
            "reviewer",
            "created_at",
            "updated_at",
            "committee_name",
            "target_faculty_name",
            "target_department_name",
            "reviewer_username",
        ]


class WorkflowCommentSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)
    verification_comment = serializers.CharField(required=False, allow_blank=True)
    held_date = serializers.DateTimeField(required=False)


class AttendanceItemSerializer(serializers.Serializer):
    member = serializers.PrimaryKeyRelatedField(queryset=QACommitteeMember.objects.all())
    attendance_status = serializers.ChoiceField(choices=CommitteeMeetingAttendance.AttendanceStatus.choices)
    remarks = serializers.CharField(required=False, allow_blank=True)


class AttendanceBulkSerializer(serializers.Serializer):
    attendance = AttendanceItemSerializer(many=True)

    def save(self, meeting):
        records = []
        for item in self.validated_data["attendance"]:
            record, _ = CommitteeMeetingAttendance.objects.update_or_create(
                meeting=meeting,
                member=item["member"],
                defaults={
                    "attendance_status": item["attendance_status"],
                    "remarks": item.get("remarks", ""),
                },
            )
            records.append(record)
        return records


def mark_report_submitted(report, user):
    report.status = QACommitteeReport.Status.SUBMITTED
    report.submitted_by = user
    report.submitted_at = timezone.now()
    report.save(update_fields=["status", "submitted_by", "submitted_at", "updated_at"])
    return report
