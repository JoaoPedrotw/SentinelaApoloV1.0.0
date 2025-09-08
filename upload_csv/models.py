#SentinelaApolo/upload_csv/models.py
from django.db import models
class Olt(models.Model):
    """
    Representa uma OLT (Optical Line Terminal).
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Onu(models.Model):
    """
    Representa uma ONU (Optical Network Unit).
    """
    device_name = models.CharField(max_length=255)
    slot_number = models.IntegerField(default=999)
    pon_number = models.IntegerField(default=999)
    cto = models.CharField(max_length=255, blank=True, null=True)
    pppoe_user = models.CharField(max_length=255, blank=True, null=True)
    olt = models.ForeignKey(Olt, on_delete=models.CASCADE, related_name='onus')
    physical_address = models.CharField(max_length=255, blank=True, null=True)
    user_code = models.CharField(max_length=255, blank=True, null=True)
    onu_status = models.CharField(max_length=50, default='unknown', blank=True, null=True)

    def __str__(self):
        return f"{self.device_name} - {self.pppoe_user}"