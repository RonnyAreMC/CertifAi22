"""URLs de administración — todas requieren autenticación admin."""
from django.urls import include, path

urlpatterns = [
    path('dashboard/', include('api.admin.dashboard.urls')),
    path('sessions/', include('api.admin.sessions.urls')),
    path('batches/', include('api.admin.batches.urls')),
    path('participants/', include('api.admin.participants.urls')),
    path('certificates/', include('api.admin.certificates.urls')),
    path('users/', include('api.admin.users.urls')),
    path('audit/', include('api.admin.audit.urls')),
    path('firmas/', include('api.admin.firmas.urls')),
    path('design/', include('api.admin.design.urls')),
    path('landing/', include('api.admin.landing.urls')),
    path('ai/', include('api.admin.ai.urls')),
]
