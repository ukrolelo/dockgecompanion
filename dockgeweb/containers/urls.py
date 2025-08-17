"""URL configuration for containers app."""

from django.urls import path
from . import views

app_name = 'containers'

urlpatterns = [
    # Main views
    path('', views.dashboard, name='dashboard'),
    path('status/', views.container_status, name='container_status'),
    path('container/<str:container_name>/', views.container_detail, name='container_detail'),
    path('container/<str:container_name>/history/', views.container_history, name='container_history'),
    path('report/', views.generate_report, name='generate_report'),
    path('settings/', views.settings, name='settings'),
    
    # API endpoints for AJAX
    path('api/scan/', views.api_scan_containers, name='api_scan_containers'),
    path('api/check-updates/', views.api_check_updates, name='api_check_updates'),
    path('api/container-status/', views.api_container_status, name='api_container_status'),
    path('api/container/<str:container_name>/updates/', views.api_container_updates, name='api_container_updates'),
]
