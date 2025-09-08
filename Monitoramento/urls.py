#SENTINELAAPOLO/Monitoramento/urls.py
from django.urls import path
from . import views
from .views import home_view

urlpatterns = [
    path('', views.iniciar_monitoramento, name='monitoramento'),
    path('logs/', views.get_logs, name='get_logs'),
    path('system-logs/', views.get_system_logs, name='system_logs'),
    path('network-alerts/', views.get_network_alerts, name='network_alerts'),
    path('recoveries/', views.get_recoveries, name='get_recoveries'),   
]