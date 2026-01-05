from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import WebsiteProject, EditHistory

User = get_user_model()


class EditHistorySerializer(serializers.ModelSerializer):
    """Serializer for edit history"""

    class Meta:
        model = EditHistory
        fields = ['id', 'edit_instruction', 'edit_type', 'model_used',
                  'execution_time', 'created_at']
        read_only_fields = ['id', 'created_at']


class WebsiteProjectSerializer(serializers.ModelSerializer):
    """Serializer for website projects"""
    user = serializers.StringRelatedField(read_only=True)
    edits = EditHistorySerializer(many=True, read_only=True)

    class Meta:
        model = WebsiteProject
        fields = ['id', 'user', 'name', 'description', 'topmate_username',
                  'html_content', 'status', 'interview_data', 'model_used',
                  'generation_time', 'token_usage', 'edits',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'status', 'model_used',
                            'generation_time', 'token_usage',
                            'created_at', 'updated_at']

    def create(self, validated_data):
        """
        Create a new WebsiteProject.

        CRITICAL FIX: Remove 'user' from validated_data to prevent
        duplicate parameter error when creating the object.
        """
        user = self.context['request'].user

        # If user is not authenticated, use demo user
        if not user.is_authenticated:
            user, created = User.objects.get_or_create(
                username='demo_user',
                defaults={'email': 'demo@example.com'}
            )

        # FIX: Prevent duplicate 'user' parameter
        validated_data.pop('user', None)

        return WebsiteProject.objects.create(user=user, **validated_data)


class UpdateHTMLSerializer(serializers.Serializer):
    """Serializer for updating HTML content"""
    html = serializers.CharField(required=True)


class EditWebsiteSerializer(serializers.Serializer):
    """Serializer for editing website"""
    edit_instruction = serializers.CharField(required=True)
    edit_type = serializers.ChoiceField(
        choices=['simple', 'complex'],
        required=False,
        default='auto'
    )
