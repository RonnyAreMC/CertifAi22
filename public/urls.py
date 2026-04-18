"""URLs públicas — solo routing declarativo (TemplateView + RedirectView).

Toda la lógica vive en `api/public/*`. Aquí solo se declara qué template
sirve cada URL y a qué endpoint API redirigen los enlaces legacy.
"""
from django.urls import path
from django.views.generic import RedirectView, TemplateView

app_name = 'public'


def page(template):
    return TemplateView.as_view(template_name=template)


urlpatterns = [
    # ── Páginas (shells HTML) ────────────────────────────────
    path('', page('public/landing.html'), name='landing'),
    path('inicio/', page('public/home.html'), name='home'),
    path('eventos/', page('public/eventos_list.html'), name='eventos_disponibles'),
    path('search/', page('public/search.html'), name='search'),
    path('attendance/', page('public/attendance_search.html'), name='attendance_search'),
    path('attendance/verify/', page('public/attendance_verify.html'), name='attendance_verify'),
    path('sesion/<int:id>/registro/', page('public/session_register.html'), name='session_register'),
    path('checkin/<str:codigo_qr>/', page('public/qr_checkin.html'), name='qr_checkin'),
    path('verificar/<str:hash>/', page('public/verify_certificate.html'), name='verify_certificate'),

    # ── Redirects legacy → API ───────────────────────────────
    path('download/<str:hash>/',
         RedirectView.as_view(url='/api/v1/public/certificates/%(hash)s/download/', permanent=False),
         name='download_pdf'),
    path('download-all/',
         RedirectView.as_view(url='/api/v1/public/certificates/bulk-download/', query_string=True, permanent=False),
         name='download_zip'),
    path('search/autocomplete/',
         RedirectView.as_view(url='/api/v1/public/certificates/autocomplete/', query_string=True, permanent=False),
         name='search_autocomplete'),
    path('attendance/autocomplete/',
         RedirectView.as_view(url='/api/v1/public/attendance/search/', query_string=True, permanent=False),
         name='attendance_autocomplete'),
    path('attendance/sessions/',
         RedirectView.as_view(url='/api/v1/public/attendance/sessions/', permanent=False),
         name='attendance_sessions_api'),
    path('attendance/confirm/',
         RedirectView.as_view(url='/api/v1/public/attendance/confirm/', permanent=False),
         name='attendance_confirm'),
    path('attendance/update-phone/',
         RedirectView.as_view(url='/api/v1/public/attendance/update-phone/', permanent=False),
         name='attendance_update_phone'),
    path('sesion/<int:id>/registro/buscar/',
         RedirectView.as_view(url='/api/v1/public/sessions/%(id)s/search-participant/', query_string=True, permanent=False),
         name='session_register_search'),
    path('sesion/<int:id>/registro/confirmar/',
         RedirectView.as_view(url='/api/v1/public/sessions/%(id)s/confirm-participant/', permanent=False),
         name='session_register_confirm'),
    path('sesion/<int:id>/registro/nuevo/',
         RedirectView.as_view(url='/api/v1/public/sessions/%(id)s/register-participant/', permanent=False),
         name='session_register_new'),
    path('checkin/<str:codigo_qr>/search/',
         RedirectView.as_view(url='/api/v1/public/checkin/%(codigo_qr)s/search/', query_string=True, permanent=False),
         name='qr_checkin_search'),
    path('checkin/<str:codigo_qr>/register/',
         RedirectView.as_view(url='/api/v1/public/checkin/%(codigo_qr)s/register/', permanent=False),
         name='qr_checkin_register'),
]
