from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('inicio/', views.home, name='home'),

    # Attendance
    path('attendance/', views.attendance_search, name='attendance_search'),
    path('attendance/verify/', views.attendance_verify, name='attendance_verify'),
    path('attendance/autocomplete/', views.attendance_autocomplete, name='attendance_autocomplete'),
    path('attendance/sessions/', views.attendance_sessions_api, name='attendance_sessions_api'),
    path('attendance/confirm/', views.attendance_confirm, name='attendance_confirm'),
    path('attendance/update-phone/', views.attendance_update_phone, name='attendance_update_phone'),

    # QR Check-in (public scan) — flujo NUEVO por cédula
    path('checkin/<str:codigo_qr>/', views.qr_checkin, name='qr_checkin'),
    path('checkin/<str:codigo_qr>/verify/', views.qr_checkin_verify, name='qr_checkin_verify'),
    path('checkin/<str:codigo_qr>/register-open/', views.qr_checkin_register_open, name='qr_checkin_register_open'),
    # QR Check-in — flujo LEGACY (búsqueda + reserva). Conservado por si se reactiva.
    path('checkin/<str:codigo_qr>/search/', views.qr_checkin_search, name='qr_checkin_search'),
    path('checkin/<str:codigo_qr>/register/', views.qr_checkin_register, name='qr_checkin_register'),

    # Certificate search & download
    path('search/', views.search, name='search'),
    path('search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('download/<str:hash>/', views.download_pdf, name='download_pdf'),
    path('download-all/', views.download_zip, name='download_zip'),

    # Smart Session Registration (Public)
    path('sesion/<int:id>/registro/', views.session_register, name='session_register'),
    path('sesion/<int:id>/registro/buscar/', views.session_register_search, name='session_register_search'),
    path('sesion/<int:id>/registro/confirmar/', views.session_register_confirm, name='session_register_confirm'),
    path('sesion/<int:id>/registro/nuevo/', views.session_register_new, name='session_register_new'),

    # Certificate Verification (QR Code)
    path('verificar/<str:hash>/', views.verify_certificate, name='verify_certificate'),
]
