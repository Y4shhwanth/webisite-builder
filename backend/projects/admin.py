from django.contrib import admin
from .models import WebsiteProject, EditHistory


@admin.register(WebsiteProject)
class WebsiteProjectAdmin(admin.ModelAdmin):
    """Admin interface for WebsiteProject"""
    list_display = ['id', 'name', 'user', 'status', 'topmate_username',
                    'model_used', 'generation_time', 'created_at']
    list_filter = ['status', 'model_used', 'created_at']
    search_fields = ['name', 'user__username', 'topmate_username']
    readonly_fields = ['created_at', 'updated_at', 'generation_time', 'token_usage']

    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'name', 'description', 'topmate_username')
        }),
        ('Content', {
            'fields': ('html_content', 'status')
        }),
        ('Interview Data', {
            'fields': ('interview_data',),
            'classes': ('collapse',)
        }),
        ('Generation Metadata', {
            'fields': ('model_used', 'generation_time', 'token_usage')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(EditHistory)
class EditHistoryAdmin(admin.ModelAdmin):
    """Admin interface for EditHistory"""
    list_display = ['id', 'project', 'edit_type', 'model_used',
                    'execution_time', 'created_at']
    list_filter = ['edit_type', 'model_used', 'created_at']
    search_fields = ['project__name', 'edit_instruction']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Edit Info', {
            'fields': ('project', 'edit_instruction', 'edit_type')
        }),
        ('HTML Changes', {
            'fields': ('html_before', 'html_after'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('model_used', 'execution_time', 'created_at')
        }),
    )
