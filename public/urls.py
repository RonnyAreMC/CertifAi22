from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('inicio/', views.home, name='home'),
    path('attendance/', views.attendance_search, name='attendance_search'),
    path('attendance/verify/', views.attendance_verify, name='attendance_verify'),
    path('search/', views.search, name='search'),
    path('download/<str:hash>/', views.download_pdf, name='download_pdf'),
    path('download-all/', views.download_zip, name='download_zip'),
]
