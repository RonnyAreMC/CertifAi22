from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Admin Panel (panel: namespace)
    path('panel/', include(('admin_panel.urls', 'admin_panel'), namespace='panel')),

    # Public App (public: namespace) — root path
    path('', include('public.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
