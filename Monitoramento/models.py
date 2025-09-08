#D:SENTINELAAPOLO/Monitoramento/models.py
from django.db import models
from upload_csv.models import Onu, Olt
from django.utils import timezone
from django.conf import settings

MIN_DROP = settings.MONITORAMENTO_MIN_DROP



class DisconnectionRecord(models.Model):
    pppoe_user = models.CharField(max_length=256)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Desconexão de {self.pppoe_user} em {self.timestamp}"

    # Deixamos sem db_table explícito para usar o padrão: monitoramento_disconnectionrecord


class SubscriberSnapshot(models.Model):
    logins = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Snapshot em {self.timestamp}"
    # Padrão: monitoramento_subscribersnapshot


class DisconnectionAnalysis(models.Model):
    data = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Análise em {self.timestamp}"
    # Padrão: monitoramento_disconnectionanalysis


class SystemLog(models.Model):
    LEVEL_CHOICES = [
        ('INFO', 'Informação'),
        ('WARNING', 'Aviso'),
        ('ERROR', 'Erro'),
        ('DEBUG', 'Depuração'),
    ]

    level = models.CharField(max_length=256, choices=LEVEL_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Tabela em letras minúsculas
        db_table = "monitoramento_systemlog"

    def __str__(self):
        return f"{self.level} - {self.timestamp}"


class NetworkAlert(models.Model):
    PROBLEM_TYPES = [
        ('INFO', 'Informação'),
        ('WARNING', 'Aviso'),
        ('ERROR', 'Erro'),
        ('DEBUG', 'Depuração'),
        ('DESCONEXOES', 'Desconexões'),
    ]

    problem_type = models.CharField(max_length=250, choices=PROBLEM_TYPES)
    message = models.TextField()
    detail = models.TextField(blank=True, null=True)
    hierarchy_data = models.JSONField(default=dict, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Tabela em letras minúsculas
        db_table = "monitoramento_networkalert"

    def __str__(self):
        return f"{self.problem_type} - {self.timestamp}"


class Alert(models.Model):
    PROBLEM_TYPES = [
        ('INFO', 'Informação'),
        ('WARNING', 'Aviso'),
        ('ERROR', 'Erro'),
        ('DEBUG', 'Depuração'),
    ]

    problem_type = models.CharField(max_length=256, choices=PROBLEM_TYPES)
    message = models.TextField()
    detail = models.TextField(blank=True, null=True)
    hierarchy_data = models.JSONField(default=dict, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Tabela em letras minúsculas
        db_table = "monitoramento_alert"

    def __str__(self):
        return f"{self.problem_type} - {self.timestamp}"

class ThresholdConfig(models.Model):
    alvo = models.CharField(max_length=50, choices=[
        ('GLOBAL', 'Global'),
        ('CTO', 'CTO'),
        ('PON', 'PON'),
        ('SLOT', 'SLOT'),
        ('OLT', 'OLT'),
    ])
    minimo_quedas = models.PositiveIntegerField(default=MIN_DROP)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.alvo}: {self.minimo_quedas}"
