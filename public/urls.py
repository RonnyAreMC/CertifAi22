from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('download/<str:hash>/', views.download_pdf, name='download_pdf'),
    path('download-all/', views.download_zip, name='download_zip'),
]
