"""URLs públicas — todas sin auth requerida (AllowAny), con throttling anónimo."""
from django.urls import include, path

urlpatterns = [
    path('stats/', include('api.public.stats.urls')),
    path('sessions/', include('api.public.sessions.urls')),
    path('certificates/', include('api.public.certificates.urls')),
    path('attendance/', include('api.public.attendance.urls')),
    path('checkin/', include('api.public.checkin.urls')),
    path('verify/', include('api.public.verify.urls')),
]
