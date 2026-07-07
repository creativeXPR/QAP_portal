from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import DashboardPermission
from .serializers import DashboardFilterSerializer
from .services import (
    get_accreditation_dashboard,
    get_activity_feed,
    get_dashboard_summary,
    get_documents_dashboard,
    get_early_warning_dashboard,
    get_examination_dashboard,
    get_infrastructure_labs_dashboard,
    get_qa_committee_dashboard,
    get_research_dashboard,
    get_student_experience_dashboard,
    get_teaching_learning_dashboard,
    get_university_overview,
    parse_dashboard_filters,
)


class DashboardBaseView(APIView):
    permission_classes = [DashboardPermission]
    service_function = None

    def get_filters(self, request):
        serializer = DashboardFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return parse_dashboard_filters(request)

    def get(self, request):
        data = self.service_function(self.get_filters(request))
        return Response({"success": True, "message": "Dashboard data fetched successfully.", "data": data})


class DashboardSummaryView(DashboardBaseView):
    service_function = staticmethod(get_dashboard_summary)


class UniversityOverviewDashboardView(DashboardBaseView):
    service_function = staticmethod(get_university_overview)


class AccreditationDashboardView(DashboardBaseView):
    service_function = staticmethod(get_accreditation_dashboard)


class QACommitteeDashboardView(DashboardBaseView):
    service_function = staticmethod(get_qa_committee_dashboard)


class TeachingLearningDashboardView(DashboardBaseView):
    service_function = staticmethod(get_teaching_learning_dashboard)


class ExaminationDashboardView(DashboardBaseView):
    service_function = staticmethod(get_examination_dashboard)


class DocumentsDashboardView(DashboardBaseView):
    service_function = staticmethod(get_documents_dashboard)


class StudentExperienceDashboardView(DashboardBaseView):
    service_function = staticmethod(get_student_experience_dashboard)


class InfrastructureLabsDashboardView(DashboardBaseView):
    service_function = staticmethod(get_infrastructure_labs_dashboard)


class ResearchDashboardView(DashboardBaseView):
    service_function = staticmethod(get_research_dashboard)


class EarlyWarningDashboardView(DashboardBaseView):
    service_function = staticmethod(get_early_warning_dashboard)


class ActivityFeedView(DashboardBaseView):
    service_function = staticmethod(get_activity_feed)
