from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import StudentFeedback
from .serializers import StudentFeedbackSerializer


class StudentFeedbackViewSet(viewsets.ModelViewSet):
    queryset = StudentFeedback.objects.all()
    serializer_class = StudentFeedbackSerializer
    permission_classes = [IsAuthenticated]
