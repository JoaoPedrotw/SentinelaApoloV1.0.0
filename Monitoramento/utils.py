#D:SENTINELAAPOLO/Monitoramento/utils.py
import paramiko
import re
import json
from datetime import datetime
from collections import defaultdict, Counter
from django.utils.timezone import now
from .models import SubscriberSnapshot, DisconnectionRecord
import logging
from django.utils import timezone
from Monitoramento.models import Alert, SystemLog, NetworkAlert
from django.db import connection

# Configurações
ROUTER_IP = "177.85.164.1"
ROUTER_PORT = "31000"
ROUTER_USERNAME = "joaopedro"
ROUTER_PASSWORD = "@#twjoaopedro1205rf!"

MIN_DROP = 4

def create_ssh_client():
    """
    Cria e retorna uma conexão SSH com o concentrador PPPoE.
    """
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=ROUTER_IP,
        port=ROUTER_PORT,
        username=ROUTER_USERNAME,
        password=ROUTER_PASSWORD,
        look_for_keys=False
    )
    return ssh

def get_active_count(ssh_client):
    """
    Executa 'show subscribers count' e retorna o número de assinantes ativos.
    """
    stdin, stdout, stderr = ssh_client.exec_command("show subscribers count")
    output = stdout.read().decode('utf-8', errors='replace').strip()
    match = re.search(r"^Total subscribers:\s+(\d+), Active Subscribers:\s+(\d+)", output)
    if match:
        return int(match.group(2))
    else:
        raise ValueError(f"Saída inesperada de 'show subscribers count': {output}")

def get_subscribers(ssh_client):
    """
    Executa 'show subscribers | display json' e retorna uma lista de usuários PPPoE ativos.
    """
    stdin, stdout, stderr = ssh_client.exec_command("show subscribers | display json")
    output = stdout.read().decode('utf-8', errors='replace')
    data = json.loads(output)
    subscribers_info = data.get("subscribers-information", [])

    logins = []
    for block in subscribers_info:
        subscriber_list = block.get("subscriber", [])
        for subscriber in subscriber_list:
            if "user-name" in subscriber:
                user_obj = subscriber["user-name"][0]
                if "data" in user_obj:
                    logins.append(user_obj["data"])
    return logins

def analyze_disconnections(disappeared):
    """
    Analisa desconexões e registra alertas.
    """
    for user_pppoe in disappeared:
        DisconnectionRecord.objects.create(pppoe_user=user_pppoe)

    # Aqui você pode adicionar lógica para agrupar por OLT, Slot, PON, etc.
    print(f"{len(disappeared)} assinantes caíram: {disappeared}")

import logging
from django.utils import timezone

from django.utils import timezone
from Monitoramento.models import Alert

logger = logging.getLogger(__name__)

def log_to_db(log_type, level, message, detail=None, hierarchy_data=None):
    message = message or ""  # Garante que message não seja None
    """
    Registra logs no console e no banco de dados, diferenciando logs de sistema e de rede.

    :param log_type: 'system' para logs de sistema; 'network' para avisos de monitoramento de rede.
    :param level: Nível do log ou tipo de problema (ex.: 'INFO', 'WARNING', 'ERROR', 'DESCONEXOES', etc.).
    :param message: Mensagem principal do log.
    :param detail: Detalhes adicionais (opcional).
    :param hierarchy_data: Dados hierárquicos (opcional), uso comum em quedas de ONU.
    """

    # 1. Registrar no console, com base no nível
    timestamp_str = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp_str}] {message}"

    if level == 'INFO':
        logger.info(log_message)
    elif level == 'WARNING':
        logger.warning(log_message)
    elif level == 'ERROR':
        logger.error(log_message)
    else:
        logger.debug(log_message)

    # 2. Registrar no banco de dados
    #    Se for um log de sistema, salva em SystemLog
    #    Se for um log de rede (monitoramento), salva em NetworkAlert
    try:
        if log_type == 'system':
            SystemLog.objects.create(
                level=level,
                message=message,
                timestamp=timezone.now()
            )

        elif log_type == 'network':
            NetworkAlert.objects.create(
                problem_type=level,
                message=message,
                detail=detail,
                hierarchy_data=hierarchy_data or {},
                timestamp=timezone.now()
            )

    except Exception as e:
        logger.error(f"[{timestamp_str}] Erro ao salvar log no banco de dados: {e}")

