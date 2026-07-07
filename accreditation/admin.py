from django.contrib import admin

from .models import (
    AccreditationComponent,
    AccreditationCycle,
    AccreditationMetric,
    ComponentScore,
    CorrectiveAction,
    EarlyWarningAlert,
    Evidence,
    MetricSubmission,
    PARIResult,
    RiskClassification,
)


admin.site.register(AccreditationCycle)
admin.site.register(AccreditationComponent)
admin.site.register(AccreditationMetric)
admin.site.register(MetricSubmission)
admin.site.register(Evidence)
admin.site.register(ComponentScore)
admin.site.register(PARIResult)
admin.site.register(RiskClassification)
admin.site.register(EarlyWarningAlert)
admin.site.register(CorrectiveAction)
