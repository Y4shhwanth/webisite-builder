from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ['username', 'email', 'topmate_username', 'created_at', 'is_staff']
    list_filter = ['is_staff', 'is_superuser', 'created_at']
    search_fields = ['username', 'email', 'topmate_username']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('topmate_username',)}),
    )
