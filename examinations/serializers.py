from rest_framework import serializers
from .models import ExamSession, ExamQualityReport


class ExamSessionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    faculty_name = serializers.CharField(source="department.faculty.name", read_only=True)

    class Meta:
        model = ExamSession
        fields = [
            "id", "department", "department_name", "faculty_name",
            "course_code_title", "exam_date", "venue", "academic_session",
        ]


class ExamQualityReportSerializer(serializers.ModelSerializer):
    course_code_title = serializers.CharField(source="exam_session.course_code_title", read_only=True)

    class Meta:
        model = ExamQualityReport
        fields = [
            "id", "exam_session", "course_code_title", "student",
            "adequacy_of_seating", "lighting_conditions", "ventilation_room_comfort",
            "noise_free_environment", "accessibility_suitability_of_venue",
            "invigilators_arrived_on_time", "clear_communication_of_instructions",
            "professional_conduct_of_invigilators", "fair_consistent_enforcement_of_rules",
            "responsiveness_to_student_needs",
            "prompt_start_of_examination", "organized_distribution_of_materials",
            "proper_management_of_exam_time", "orderliness_during_submission",
            "provision_for_special_needs",
            "observed_misconduct", "incident_description", "action_taken",
            "overall_rating", "suggestions_for_improvement",
            "submitted_at",
        ]
        read_only_fields = ["student", "submitted_at"]

    def validate(self, attrs):
        observed = attrs.get("observed_misconduct", getattr(self.instance, "observed_misconduct", None))
        description = attrs.get("incident_description", getattr(self.instance, "incident_description", ""))

        if observed and not description:
            raise serializers.ValidationError(
                {"incident_description": "Required when misconduct was observed."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)