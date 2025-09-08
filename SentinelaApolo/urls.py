
# D:\SentinelaApolo\urls.py
from django.contrib import admin
from django.urls import path,include
from Monitoramento.views import home_view 


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Login.urls')),
    path('upload-csv/', include('upload_csv.urls')),
    path('monitoramento/', include('Monitoramento.urls')),
    path('home/', home_view, name='home'),  # A rota /home/
     path('alertamento/', include('Alertamento.urls', namespace='alertamento')),
]