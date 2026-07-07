from rest_framework import filters, permissions, viewsets

from .models import Department, Faculty
from .serializers import DepartmentSerializer, FacultySerializer


class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.select_related("faculty").all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "faculty__name"]
