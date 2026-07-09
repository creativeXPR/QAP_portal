from django.contrib import admin
from .models import Update

@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'classification', 'forUser', 'description')
    search_fields = ('title', 'category', 'classification')
