from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """User API ViewSet"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'])
    def get_or_create(self, request):
        """Get or create user by username"""
        username = request.data.get('username')
        email = request.data.get('email', f'{username}@example.com')

        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )

        serializer = self.get_serializer(user)
        return Response({
            'user': serializer.data,
            'created': created
        }, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
