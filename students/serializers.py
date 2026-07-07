from rest_framework import serializers
from .models import StudentFeedback


class StudentFeedbackSerializer(serializers.ModelSerializer):
    student = serializers.CharField(write_only=True, source="student_name")
    feedback = serializers.CharField(write_only=True, source="feedback_text")

    class Meta:
        model = StudentFeedback
        fields = ["id", "student", "student_email", "feedback", "category", "classification", "status", "urgency", "submitted_at"]
        read_only_fields = ["id", "status", "submitted_at"]
