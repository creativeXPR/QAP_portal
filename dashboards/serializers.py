from rest_framework import serializers


class DashboardFilterSerializer(serializers.Serializer):
    faculty_id = serializers.IntegerField(required=False)
    department_id = serializers.IntegerField(required=False)
    programme_id = serializers.CharField(required=False, allow_blank=True)
    committee_id = serializers.CharField(required=False, allow_blank=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    period = serializers.ChoiceField(
        required=False,
        choices=["this_week", "this_month", "this_quarter", "this_year"],
    )
    status = serializers.CharField(required=False, allow_blank=True)
    risk_level = serializers.CharField(required=False, allow_blank=True)
    severity = serializers.CharField(required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)


class KPICardSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    value = serializers.JSONField()
    unit = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)


class ChartDatasetSerializer(serializers.Serializer):
    type = serializers.CharField()
    labels = serializers.ListField(child=serializers.CharField())
    datasets = serializers.ListField(child=serializers.DictField())
