from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import requests
import logging

from .models import WebsiteProject, EditHistory
from .serializers import (
    WebsiteProjectSerializer,
    UpdateHTMLSerializer,
    EditWebsiteSerializer
)
from django.conf import settings

logger = logging.getLogger(__name__)


class WebsiteProjectViewSet(viewsets.ModelViewSet):
    """API ViewSet for website projects"""
    queryset = WebsiteProject.objects.all()
    serializer_class = WebsiteProjectSerializer

    def get_queryset(self):
        """Filter projects by user if authenticated"""
        if self.request.user.is_authenticated:
            return WebsiteProject.objects.filter(user=self.request.user)
        return WebsiteProject.objects.filter(user__username='demo_user')

    @action(detail=True, methods=['post'])
    def update_html(self, request, pk=None):
        """Update HTML content for a project"""
        project = self.get_object()
        serializer = UpdateHTMLSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        html = serializer.validated_data['html']

        # Save old HTML for history
        old_html = project.html_content

        # Update HTML
        project.html_content = html
        project.save()

        logger.info(f"Updated HTML for project {project.id}")

        return Response({
            'success': True,
            'message': 'HTML updated successfully',
            'project_id': project.id
        })

    @action(detail=True, methods=['post'])
    def edit(self, request, pk=None):
        """Edit website using AI Engine"""
        project = self.get_object()
        serializer = EditWebsiteSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        edit_instruction = serializer.validated_data['edit_instruction']
        edit_type = serializer.validated_data.get('edit_type', 'auto')

        # Save current HTML for history
        html_before = project.html_content

        try:
            # Call AI Engine edit endpoint
            ai_engine_url = settings.AI_ENGINE_URL
            response = requests.post(
                f"{ai_engine_url}/api/edit/optimized",
                json={
                    'project_id': project.id,
                    'html': project.html_content,
                    'edit_instruction': edit_instruction,
                    'edit_type': edit_type
                },
                timeout=120
            )

            if response.status_code != 200:
                return Response({
                    'error': 'Failed to edit website',
                    'details': response.text
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            result = response.json()
            new_html = result.get('html', project.html_content)

            # Update project HTML
            project.html_content = new_html
            project.save()

            # Save edit history
            EditHistory.objects.create(
                project=project,
                edit_instruction=edit_instruction,
                html_before=html_before,
                html_after=new_html,
                edit_type=result.get('edit_type', edit_type),
                model_used=result.get('model', 'unknown'),
                execution_time=result.get('execution_time', 0)
            )

            return Response({
                'success': True,
                'html': new_html,
                'edit_type': result.get('edit_type'),
                'execution_time': result.get('execution_time')
            })

        except requests.Timeout:
            return Response({
                'error': 'Edit request timed out'
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except Exception as e:
            logger.error(f"Error editing project {project.id}: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get edit history for a project"""
        project = self.get_object()
        edits = project.edits.all()[:20]  # Last 20 edits

        from .serializers import EditHistorySerializer
        serializer = EditHistorySerializer(edits, many=True)

        return Response({
            'project_id': project.id,
            'total_edits': project.edits.count(),
            'recent_edits': serializer.data
        })
