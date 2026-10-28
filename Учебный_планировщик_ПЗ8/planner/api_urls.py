from rest_framework.routers import DefaultRouter

from .api import SubjectViewSet, TaskViewSet

router = DefaultRouter()
router.register('subjects', SubjectViewSet, basename='api-subject')
router.register('tasks', TaskViewSet, basename='api-task')

urlpatterns = router.urls
