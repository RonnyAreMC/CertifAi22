from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    # API REST (JSON)
    path('api/', include('api.urls')),

    # Admin Panel (Django MVC)
    path('panel/', include(('admin_panel.urls', 'admin_panel'), namespace='panel')),

    # Páginas públicas (shells HTML — la lógica vive en /api/v1/public/)
    path('', include('public.urls')),

    # Templates de error (debug)
    path('test-400/', TemplateView.as_view(template_name='400.html')),
    path('test-403/', TemplateView.as_view(template_name='403.html')),
    path('test-404/', TemplateView.as_view(template_name='404.html')),
    path('test-500/', TemplateView.as_view(template_name='500.html')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
