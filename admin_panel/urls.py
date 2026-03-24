from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'panel'

urlpatterns = [
    # Auth
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Register & Access Requests
    path('register/', views.register, name='register'),
    path('solicitud-pendiente/<int:id>/', views.solicitud_pendiente, name='solicitud_pendiente'),
    path('mi-estado/', views.mi_estado, name='mi_estado'),
    path('solicitudes-pendientes/', views.solicitudes_pendientes, name='solicitudes_pendientes'),
    path('solicitudes/<int:id>/aprobar/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('solicitudes/<int:id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Batch Management
    path('batches/', views.list_batches, name='batch_list'),
    path('batches/new/', views.create_batch, name='batch_create'),
    path('batches/<int:id>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:id>/configure/', views.configure_batch, name='batch_configure'),
    path('batches/<int:id>/delete/', views.delete_batch, name='batch_delete'),
    path('batches/<int:id>/preview/', views.preview_pdf, name='batch_preview'),
    path('batches/<int:id>/process-mapping/', views.process_batch_mapping, name='batch_process_mapping'),

    # Certificate Management
    path('batches/<int:id>/add-certificate/', views.add_certificate, name='add_certificate'),

    # Session Management (QR Attendance)
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:id>/toggle/', views.session_toggle, name='session_toggle'),
    path('sessions/<int:id>/delete/', views.session_delete, name='session_delete'),
    path('sessions/<int:id>/qr/', views.session_qr_display, name='session_qr_display'),
    path('sessions/<int:id>/attendees/', views.session_attendees_api, name='session_attendees_api'),
    path('sessions/<int:id>/bulk-pdf/', views.session_bulk_pdf, name='session_bulk_pdf'),
    path('sessions/<int:id>/edit/', views.session_edit, name='session_edit'),
    path('sessions/<int:id>/generate-batch/', views.session_generate_batch, name='session_generate_batch'),

    # Landing Page Builder
    path('landing/', views.landing_builder, name='landing_builder'),
    path('landing/add/', views.landing_add_block, name='landing_add_block'),
    path('landing/<int:id>/update/', views.landing_update_block, name='landing_update_block'),
    path('landing/<int:id>/delete/', views.landing_delete_block, name='landing_delete_block'),
    path('landing/reorder/', views.landing_reorder, name='landing_reorder'),

    # Líderes Académicos
    path('lideres/', views.lideres_list, name='lideres_list'),
    path('lideres/add/', views.lideres_add_manual, name='lideres_add_manual'),
    path('lideres/upload/', views.lideres_upload_excel, name='lideres_upload_excel'),
    path('lideres/process-mapping/', views.lideres_process_mapping, name='lideres_process_mapping'),
    path('lideres/<int:id>/remove/', views.lideres_remove, name='lideres_remove'),
]
