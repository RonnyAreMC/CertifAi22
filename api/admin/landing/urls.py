from rest_framework.routers import DefaultRouter
from .views import LandingBloqueViewSet

router = DefaultRouter()
router.register('blocks', LandingBloqueViewSet, basename='landing-blocks')

urlpatterns = router.urls
