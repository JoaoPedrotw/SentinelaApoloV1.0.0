#D:/SentinelaApolo/Alertamento/forms.py
from django import forms
from .models import Incidente

class IncidenteForm(forms.ModelForm):
    class Meta:
        model = Incidente
        fields = ['tipo', 'nivel', 'mensagem', 'detalhes']
