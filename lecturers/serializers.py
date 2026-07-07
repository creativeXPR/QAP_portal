from rest_framework import serializers
from .models import LecturerProfile, AssessmentReport


class LecturerProfileSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    faculty_name = serializers.CharField(source="department.faculty.name", read_only=True)
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = LecturerProfile
        fields = [
            "id", "user", "full_name", "department", "department_name",
            "faculty_name", "staff_id", "rank",
        ]


class AssessmentReportSerializer(serializers.ModelSerializer):
    lecturer_name = serializers.CharField(source="lecturer.user.get_full_name", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    average_rating = serializers.ReadOnlyField()

    class Meta:
        model = AssessmentReport
        fields = [
            "id", "lecturer", "lecturer_name", "student", "course", "course_code",
            "academic_session", "semester",
            "presents_content_actively", "covers_content_within_timeframe",
            "gives_useful_assignments", "impressive_comportment",
            "punctual_at_lectures", "available_for_consultation",
            "clear_on_concepts", "links_theory_to_practice",
            "encourages_participation", "provides_assignment_feedback",
            "teaches_per_course_outline", "teaches_class_regularly",
            "updates_course_content", "uses_real_life_examples",
            "appears_neatly", "uses_varied_teaching_methods",
            "uses_technology_innovatively",
            "average_rating", "included_in_dossier", "submitted_at",
        ]
        read_only_fields = ["student", "included_in_dossier", "submitted_at"]

    def create(self, validated_data):
        validated_data["student"] = self.context["request"].user
        return super().create(validated_data)