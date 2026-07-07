from rest_framework import serializers
from .models import Course, LectureSession


class CourseSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Course
        fields = ["id", "code", "title", "department", "department_name"]


class LectureSessionSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    department_name = serializers.CharField(source="course.department.name", read_only=True)
    faculty_name = serializers.CharField(source="course.department.faculty.name", read_only=True)
    respondent_email = serializers.CharField(source="respondent.email", read_only=True)

    class Meta:
        model = LectureSession
        fields = [
            "id", "course", "course_code", "department_name", "faculty_name",
            "respondent", "respondent_email",
            "monitored_at", "time_slot", "level", "mode",
            "lecturer_present", "actual_duration", "venue",
            "held", "explanation", "reason_not_held",
            "estimated_attendance", "classroom_environment_rating",
            "teaching_effectiveness_rating", "quality_concerns",
            "created_at",
        ]
        read_only_fields = ["respondent", "created_at"]

    def validate(self, attrs):
        held = attrs.get("held", getattr(self.instance, "held", None))
        reason = attrs.get("reason_not_held", getattr(self.instance, "reason_not_held", ""))

        if held is False and not reason:
            raise serializers.ValidationError(
                {"reason_not_held": "Required when the lecture did not hold."}
            )
        if held is True and reason:
            raise serializers.ValidationError(
                {"reason_not_held": "Should be blank when the lecture held."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["respondent"] = self.context["request"].user
        return super().create(validated_data)