from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WebsiteProjectViewSet

router = DefaultRouter()
router.register(r'', WebsiteProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]
