"""URLs del panel admin.

Las páginas que son puras shells HTML (dashboard, listas) se sirven con
TemplateView + decoradores de auth. Las que tienen forms/uploads complejos
siguen como funciones en `admin_panel/views/*`.
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import path
from django.views.generic import RedirectView, TemplateView

from .views._shared import _is_admin, _is_superadmin
from .views import (
    # auth
    CustomLoginView, register, solicitud_pendiente, solicitudes_pendientes,
    aprobar_solicitud, rechazar_solicitud, mi_estado,
    # batch
    list_batches, create_batch, batch_detail, configure_batch,
    process_batch_mapping,
    # certificate
    add_certificate,
    # session
    session_list, session_create, session_edit,
    session_qr_display, session_generate_batch,
    # design
    design_global, design_global_preview, design_save_firma_pos,
    # landing
    landing_builder,
    # leaders
    lideres_list, lideres_add_manual, lideres_upload_excel,
    lideres_process_mapping,
)
from . import views_firmas

app_name = 'panel'


def admin_page(template):
    """Shell HTML protegido — requiere login + rol admin."""
    return login_required(
        user_passes_test(_is_admin)(TemplateView.as_view(template_name=template))
    )


def superadmin_page(template):
    """Shell HTML protegido — requiere login + rol superadmin."""
    return login_required(
        user_passes_test(_is_superadmin)(TemplateView.as_view(template_name=template))
    )


urlpatterns = [
    # Auth
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),
    path('solicitud-pendiente/<int:id>/', solicitud_pendiente, name='solicitud_pendiente'),
    path('solicitudes-pendientes/', solicitudes_pendientes, name='solicitudes_pendientes'),
    path('solicitudes/<int:id>/aprobar/', aprobar_solicitud, name='aprobar_solicitud'),
    path('solicitudes/<int:id>/rechazar/', rechazar_solicitud, name='rechazar_solicitud'),

    # Dashboard (shell + API)
    path('', admin_page('panel/dashboard/index.html'), name='dashboard'),

    # Batches — list/detail/create/mapping/configure son forms. delete y preview → API.
    path('batches/', list_batches, name='batch_list'),
    path('batches/new/', create_batch, name='batch_create'),
    path('batches/<int:id>/', batch_detail, name='batch_detail'),
    path('batches/<int:id>/configure/', configure_batch, name='batch_configure'),
    path('batches/<int:id>/process-mapping/', process_batch_mapping, name='batch_process_mapping'),
    path('batches/<int:id>/delete/',
         RedirectView.as_view(url='/api/v1/admin/batches/%(id)s/', permanent=False),
         name='batch_delete'),
    path('batches/<int:id>/preview/',
         RedirectView.as_view(url='/api/v1/admin/batches/%(id)s/preview-pdf/', permanent=False),
         name='batch_preview'),

    # Design (forms)
    path('diseno/', design_global, name='design_global'),
    path('diseno/preview/', design_global_preview, name='design_global_preview'),
    path('diseno/firma-pos/', design_save_firma_pos, name='design_save_firma_pos'),

    # Certificates (form add)
    path('batches/<int:id>/add-certificate/', add_certificate, name='add_certificate'),
    path('api/participante-lookup/',
         RedirectView.as_view(url='/api/v1/admin/participants/', query_string=True, permanent=False),
         name='participante_lookup'),

    # Sessions — list es shell, create/edit son forms. Demás ops → API.
    path('sessions/', session_list, name='session_list'),
    path('sessions/create/', session_create, name='session_create'),
    path('sessions/<int:id>/edit/', session_edit, name='session_edit'),
    path('sessions/<int:id>/qr/', session_qr_display, name='session_qr_display'),
    path('sessions/<int:id>/generate-batch/', session_generate_batch, name='session_generate_batch'),
    # Legacy → API
    path('sessions/<int:id>/toggle/',
         RedirectView.as_view(url='/api/v1/admin/sessions/%(id)s/toggle/', permanent=False),
         name='session_toggle'),
    path('sessions/<int:id>/delete/',
         RedirectView.as_view(url='/api/v1/admin/sessions/%(id)s/', permanent=False),
         name='session_delete'),
    path('sessions/<int:id>/attendees/',
         RedirectView.as_view(url='/api/v1/admin/sessions/%(id)s/attendees/', query_string=True, permanent=False),
         name='session_attendees_api'),
    path('sessions/<int:id>/bulk-pdf/',
         RedirectView.as_view(url='/api/v1/admin/sessions/%(id)s/bulk-pdf/', permanent=False),
         name='session_bulk_pdf'),

    # Landing builder (shell; CRUD vía /api/v1/admin/landing/blocks/)
    path('landing/', landing_builder, name='landing_builder'),
    path('landing/add-block/',
         RedirectView.as_view(url='/api/v1/admin/landing/blocks/', permanent=False),
         name='landing_add_block'),
    path('landing/block/<int:id>/update/',
         RedirectView.as_view(url='/api/v1/admin/landing/blocks/%(id)s/', permanent=False),
         name='landing_update_block'),
    path('landing/block/<int:id>/delete/',
         RedirectView.as_view(url='/api/v1/admin/landing/blocks/%(id)s/', permanent=False),
         name='landing_delete_block'),
    path('landing/reorder/',
         RedirectView.as_view(url='/api/v1/admin/landing/blocks/reorder/', permanent=False),
         name='landing_reorder'),

    # Mi Estado
    path('mi-estado/', mi_estado, name='mi_estado'),

    # Líderes (upload Excel); remove → API toggle_leader
    path('lideres/', lideres_list, name='lideres_list'),
    path('lideres/add/', lideres_add_manual, name='lideres_add_manual'),
    path('lideres/upload/', lideres_upload_excel, name='lideres_upload_excel'),
    path('lideres/process-mapping/', lideres_process_mapping, name='lideres_process_mapping'),
    path('lideres/<int:id>/remove/',
         RedirectView.as_view(url='/api/v1/admin/participants/%(id)s/toggle_leader/', permanent=False),
         name='lideres_remove'),

    # ── Pages migradas a shell + API ──────────────────────────
    # Usuarios (superadmin)
    path('usuarios/', superadmin_page('panel/usuarios/list.html'), name='usuarios_list'),
    path('usuarios/<int:id>/reset-password/',
         RedirectView.as_view(url='/api/v1/admin/users/%(id)s/reset-password/', permanent=False),
         name='usuario_reset_password'),

    # Participantes (admin)
    path('participantes/', admin_page('panel/participantes/list.html'), name='participantes_list'),
    path('participantes/<int:id>/delete/',
         RedirectView.as_view(url='/api/v1/admin/participants/%(id)s/', permanent=False),
         name='participante_delete'),

    # Firmas (list + delete shell; create/edit siguen con forms)
    path('firmas/', superadmin_page('panel/firmas/list.html'), name='firma_list'),
    path('firmas/new/', views_firmas.firma_create, name='firma_create'),
    path('firmas/<int:id>/edit/', views_firmas.firma_edit, name='firma_edit'),
    path('firmas/<int:id>/delete/',
         RedirectView.as_view(url='/api/v1/admin/firmas/%(id)s/', permanent=False),
         name='firma_delete'),
]
