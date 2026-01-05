from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'topmate_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
