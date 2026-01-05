from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WebsiteProject(models.Model):
    """Website project model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    topmate_username = models.CharField(max_length=100, blank=True)

    # HTML content
    html_content = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Interview data (JSON)
    interview_data = models.JSONField(default=dict, blank=True)

    # Generation metadata
    model_used = models.CharField(max_length=100, blank=True)
    generation_time = models.FloatField(null=True, blank=True)  # seconds
    token_usage = models.JSONField(default=dict, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'website_projects'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"


class EditHistory(models.Model):
    """Track edit history for a project"""
    project = models.ForeignKey(WebsiteProject, on_delete=models.CASCADE, related_name='edits')
    edit_instruction = models.TextField()
    html_before = models.TextField()
    html_after = models.TextField()

    # Metadata
    edit_type = models.CharField(max_length=50, blank=True)  # 'simple', 'complex'
    model_used = models.CharField(max_length=100, blank=True)
    execution_time = models.FloatField(null=True, blank=True)  # seconds

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'edit_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"Edit for {self.project.name} at {self.created_at}"
