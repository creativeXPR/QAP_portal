from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import Profile

User = get_user_model()

class ProfileInline(admin.StackedInline):
    model = Profile
    fields = ('status', 'profile_complete')
    can_delete = False

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'profile_complete')
    list_filter = ('status', 'profile_complete')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('user',)

# Customize User admin to show Profile inline
class CustomUserAdmin(DefaultUserAdmin):
    inlines = [ProfileInline]

# Unregister default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)