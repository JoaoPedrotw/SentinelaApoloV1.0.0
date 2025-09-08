# D:\SentinelaApolo\Login\urls.py

from django.urls import path
from . import views
from .views import login_view

urlpatterns = [
    path('', views.login_view, name='login'),   # rota principal do app, chama login_view
    path('logout/', views.logout_view, name='logout'),
]
