#SentinelaApolo/upload_csv/admin.py
from django.contrib import admin
from django.contrib import admin
from .models import Olt, Onu

# Registrar o modelo Olt
@admin.register(Olt)
class OltAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Exibe o campo 'name' na lista do admin

# Registrar o modelo Onu
@admin.register(Onu)
class OnuAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'slot_number', 'pon_number', 'cto', 'pppoe_user', 'olt', 'onu_status')
    list_filter = ('olt', 'onu_status')  # Adiciona filtros para facilitar a navegação
    search_fields = ('device_name', 'pppoe_user', 'user_code')  # Adiciona uma barra de busca