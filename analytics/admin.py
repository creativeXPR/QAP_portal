from django.contrib import admin
from .models import KPI

# Register your models here.
@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "category", "embedlink", "metrics")
    list_filter = ("title", "description", "category")
    search_fields = ("title", "description", "category")