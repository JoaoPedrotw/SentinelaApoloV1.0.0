# A#D:/SentinelaApolo/Alertamento/urls.py
from django.urls import path
from . import views
app_name = 'alertamento'    # <— importante para namespacing

urlpatterns = [
    path('', views.incident_list, name='incident_list'),
    path('new/', views.incident_create, name='incident_create'),
    path('<int:pk>/', views.incident_detail, name='incident_detail'),
    path('api/incidentes/', views.get_incidentes, name='api_incidentes'),
]