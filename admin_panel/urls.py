from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'panel'

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(
        template_name='panel/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

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
]
