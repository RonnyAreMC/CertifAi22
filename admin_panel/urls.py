from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_firmas

app_name = 'panel'

urlpatterns = [
    # Auth
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Register & Access Requests
    path('register/', views.register, name='register'),
    path('solicitud-pendiente/<int:id>/', views.solicitud_pendiente, name='solicitud_pendiente'),
    path('solicitudes-pendientes/', views.solicitudes_pendientes, name='solicitudes_pendientes'),
    path('solicitudes/<int:id>/aprobar/', views.aprobar_solicitud, name='aprobar_solicitud'),
    path('solicitudes/<int:id>/rechazar/', views.rechazar_solicitud, name='rechazar_solicitud'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Batch Management
    path('batches/', views.list_batches, name='batch_list'),
    path('batches/new/', views.create_batch, name='batch_create'),
    path('batches/<int:id>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:id>/configure/', views.configure_batch, name='batch_configure'),  # legacy → redirige a diseno
    path('diseno/', views.design_global, name='design_global'),
    path('diseno/preview/', views.design_global_preview, name='design_global_preview'),
    path('diseno/firma-pos/', views.design_save_firma_pos, name='design_save_firma_pos'),
    path('batches/<int:id>/delete/', views.delete_batch, name='batch_delete'),
    path('batches/<int:id>/preview/', views.preview_pdf, name='batch_preview'),
    path('batches/<int:id>/process-mapping/', views.process_batch_mapping, name='batch_process_mapping'),

    # Certificate Management
    path('api/participante-lookup/', views.participante_lookup, name='participante_lookup'),
    path('batches/<int:id>/add-certificate/', views.add_certificate, name='add_certificate'),

    # Session Management (QR Attendance)
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/<int:id>/edit/', views.session_edit, name='session_edit'),
    path('sessions/<int:id>/toggle/', views.session_toggle, name='session_toggle'),
    path('sessions/<int:id>/delete/', views.session_delete, name='session_delete'),
    path('sessions/<int:id>/qr/', views.session_qr_display, name='session_qr_display'),
    path('sessions/<int:id>/attendees/', views.session_attendees_api, name='session_attendees_api'),
    path('sessions/<int:id>/bulk-pdf/', views.session_bulk_pdf, name='session_bulk_pdf'),
    path('sessions/<int:id>/generate-batch/', views.session_generate_batch, name='session_generate_batch'),

    # Landing Builder
    path('landing/', views.landing_builder, name='landing_builder'),
    path('landing/add-block/', views.landing_add_block, name='landing_add_block'),
    path('landing/block/<int:id>/update/', views.landing_update_block, name='landing_update_block'),
    path('landing/block/<int:id>/delete/', views.landing_delete_block, name='landing_delete_block'),
    path('landing/reorder/', views.landing_reorder, name='landing_reorder'),

    # Mi Estado
    path('mi-estado/', views.mi_estado, name='mi_estado'),

    # Líderes Management
    path('lideres/', views.lideres_list, name='lideres_list'),
    path('lideres/add/', views.lideres_add_manual, name='lideres_add_manual'),
    path('lideres/upload/', views.lideres_upload_excel, name='lideres_upload_excel'),
    path('lideres/process-mapping/', views.lideres_process_mapping, name='lideres_process_mapping'),
    path('lideres/<int:id>/remove/', views.lideres_remove, name='lideres_remove'),

    # Usuarios (superadmin)
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/<int:id>/reset-password/', views.usuario_reset_password, name='usuario_reset_password'),

    # Participantes (global)
    path('participantes/', views.participantes_list, name='participantes_list'),
    path('participantes/<int:id>/delete/', views.participante_delete, name='participante_delete'),

    # Firmas Institucionales Management
    path('firmas/', views_firmas.firma_list, name='firma_list'),
    path('firmas/new/', views_firmas.firma_create, name='firma_create'),
    path('firmas/<int:id>/edit/', views_firmas.firma_edit, name='firma_edit'),
    path('firmas/<int:id>/delete/', views_firmas.firma_delete, name='firma_delete'),
]
