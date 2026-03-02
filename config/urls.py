from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Admin Panel (panel: namespace)
    path('panel/', include(('admin_panel.urls', 'admin_panel'), namespace='panel')),

    # Public App (public: namespace) — root path
    path('', include('public.urls')),
    # Rutas para probar las plantillas de error
    path('test-400/', TemplateView.as_view(template_name='400.html')),
    path('test-403/', TemplateView.as_view(template_name='403.html')),
    path('test-404/', TemplateView.as_view(template_name='404.html')),
    path('test-500/', TemplateView.as_view(template_name='500.html')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
