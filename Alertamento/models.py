#D:/SentinelaApolo/Alertamento/models.py
from django.db import models
from django.utils import timezone

class Incidente(models.Model):
    TIPO_CHOICES = [
        ('CTO_DOWN',    'CTO totalmente offline'),
        ('PON_DOWN',    'PON totalmente offline'),
        ('SLOT_DOWN',   'SLOT totalmente offline'),
        ('OLT_DOWN',    'OLT totalmente offline'),
        ('CTO_UP',      'CTO recuperada'),
        ('RECOVERY',    'Recuperação geral'),
    ]
    NIVEL_CHOICES = [
        ('INFO',    'Informação'),
        ('WARNING', 'Aviso'),
        ('ERROR',   'Erro'),
    ]

    tipo       = models.CharField(max_length=20, choices=TIPO_CHOICES)
    nivel      = models.CharField(max_length=10, choices=NIVEL_CHOICES)
    mensagem   = models.TextField()
    detalhes   = models.JSONField(blank=True, null=True)
    timestamp  = models.DateTimeField(default=timezone.now)
    resolvido  = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        db_table = "alertamento_incidente"

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.get_tipo_display()}"


class StatusHistorico(models.Model):
    niveis = [
        ('UP', 'Up'),
        ('DOWN', 'Down'),
    ]
    alvo = models.CharField(max_length=50)      # ex: "CTO-123", "PON-OLT02-S12-P4"
    status = models.CharField(max_length=4, choices=niveis)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alvo} {self.status} em {self.timestamp}"
