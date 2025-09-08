# D:/SentinelaApolo/Monitoramento/management/commands/monitorador_de_rede.py

import paramiko
import time
import re
import json
from django.core.management.base import BaseCommand
from collections import defaultdict, Counter
from django.utils import timezone
from Monitoramento.models import Onu, Alert, SubscriberSnapshot, DisconnectionRecord, DisconnectionAnalysis
from Monitoramento.utils import log_to_db
from Alertamento.models import Incidente

# Configurações
ROUTER_IP = 
ROUTER_PORT = 31000  # Porta como inteiro
ROUTER_USERNAME = 
ROUTER_PASSWORD = 
MIN_DROP = 4
CHECK_INTERVAL = 240


class Command(BaseCommand):
    help = "Monitora quedas de ONUs e registra alertas hierárquicos."

    def handle(self, *args, **options):
        # Estado entre ciclos
        self.previous_active_count = 0
        self.previous_logins = []
        self.grouped_ctos_previous = {}
        # Usuários que sofreram queda crítica e aguardam notificação de recuperação
        self.users_in_critical_drop = set()

        # Inicialização
        log_to_db('system', 'INFO', "Iniciando monitoramento (Ctrl+C para parar).", None, None)

        try:
            while True:
                # 1) Conexão SSH
                try:
                    ssh_client = self.create_ssh_client()
                    log_to_db('system', 'INFO', "SSH conectado ao concentrador PPPoE.", None, None)
                except paramiko.ssh_exception.AuthenticationException:
                    log_to_db('system', 'ERROR', "Falha de autenticação SSH!", None, None)
                    time.sleep(CHECK_INTERVAL)
                    continue
                except Exception as e:
                    log_to_db('system', 'ERROR', f"Erro na conexão SSH: {e}", None, None)
                    time.sleep(CHECK_INTERVAL)
                    continue

                # 2) Coleta de dados
                current_active_count = self.get_active_count(ssh_client)
                new_logins = self.get_subscribers(ssh_client)

                # 3) Primeiro ciclo: só snapshot
                if self.previous_active_count == 0:
                    self.previous_logins = new_logins
                    self.save_subscriber_snapshot(new_logins)
                    self.grouped_ctos_previous = self.build_cto_map(new_logins)
                    self.previous_active_count = current_active_count
                    ssh_client.close()
                    log_to_db('system', 'INFO', f"[Inicializado] Aguardando {CHECK_INTERVAL}s...", None, None)
                    time.sleep(CHECK_INTERVAL)
                    continue

                # 4) Cálculo de diferença
                diff = self.previous_active_count - current_active_count
                now = timezone.localtime(timezone.now()).strftime("%H:%M:%S")
                log_to_db('system', 'INFO', f"{now} | Queda detectada: {diff}", None, None)

                # --- DETECÇÃO DE RECUPERAÇÃO (apenas para quem participou de queda crítica) ---
                if diff < 0:
                    recovered = set(new_logins) - set(self.previous_logins)
                    # filtra só usuários que de fato tiveram queda crítica
                    recovered &= self.users_in_critical_drop

                    if recovered:
                        # agrupa recuperações por OLT/SLOT/PON
                        rec_estrutura = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
                        for user in recovered:
                            # pode haver múltiplos registros Onu para o mesmo PPPoE
                            for onu in Onu.objects.filter(pppoe_user=user):
                                olt = str(onu.olt) or "SEM_OLT"
                                rec_estrutura[olt][onu.slot_number][onu.pon_number].append(user)

                        # registra alertas de recuperação
                        for olt, slots in rec_estrutura.items():
                            for slot, pons in slots.items():
                                for pon, users in pons.items():
                                    count = len(users)
                                    msg = (
                                        f"Recuperação: {count} assinantes reconectados "
                                        f"em OLT {olt}, SLOT {slot}, PON {pon}"
                                    )
                                    log_to_db(
                                        'network', 'INFO', msg,
                                        detail="Recuperação PPPoE",
                                        hierarchy_data={'OLT': olt, 'SLOT': slot, 'PON': pon}
                                    )
                                    Incidente.objects.create(
                                        tipo='RECOVERY',
                                        nivel='INFO',
                                        mensagem=msg,
                                        detalhes={'olt': olt, 'slot': slot, 'pon': pon}
                                    )

                        # remove do conjunto para não notificar novamente
                        self.users_in_critical_drop -= recovered

                    # atualiza estado e segue
                    self.previous_logins = new_logins
                    self.grouped_ctos_previous = self.build_cto_map(new_logins)
                    self.previous_active_count = current_active_count
                    ssh_client.close()
                    time.sleep(CHECK_INTERVAL)
                    continue

                # --- QUEDAS CRÍTICAS ---
                if diff >= MIN_DROP:
                    disappeared = set(self.previous_logins) - set(new_logins)
                    # marca para futura recuperação
                    self.users_in_critical_drop |= disappeared

                    # alerta de CTO totalmente offline (>=3 antes)
                    for cto_val, users_before in self.grouped_ctos_previous.items():
                        if len(users_before) >= 3:
                            still = [u for u in users_before if u in new_logins]
                            if not still:
                                log_to_db(
                                    'network', 'ERROR',
                                    f"CTO {cto_val} totalmente offline (todas as conexões caíram).",
                                    detail="Queda total de CTO",
                                    hierarchy_data={'cto': cto_val}
                                )

                    # log geral
                    log_to_db('network', 'WARNING', f"Queda crítica ({diff}) detectada.", None, None)
                    # salva snapshot e dispara análise hierárquica
                    self.save_subscriber_snapshot(new_logins)
                    self.analyze_disconnections(disappeared)

                    # atualiza estado
                    self.previous_logins = new_logins
                    self.grouped_ctos_previous = self.build_cto_map(new_logins)
                else:
                    # sem queda crítica, só atualiza estado
                    self.grouped_ctos_previous = self.build_cto_map(new_logins)
                    self.previous_logins = new_logins

                self.previous_active_count = current_active_count
                ssh_client.close()
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            log_to_db('system', 'WARNING', "Monitoramento interrompido pelo usuário.", None, None)
        except Exception as e:
            log_to_db('system', 'ERROR', f"Erro inesperado: {e}", None, None)


    # -----------------------------------------------------
    # FUNÇÕES AUXILIARES
    # -----------------------------------------------------

    def create_ssh_client(self):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=ROUTER_IP,
            port=ROUTER_PORT,
            username=ROUTER_USERNAME,
            password=ROUTER_PASSWORD,
            look_for_keys=False,
            timeout=10
        )
        return ssh

    def get_active_count(self, ssh_client):
        stdin, stdout, stderr = ssh_client.exec_command("show subscribers count")
        output = stdout.read().decode('utf-8', errors='replace').strip()
        match = re.search(r"^Total subscribers:\s+(\d+), Active Subscribers:\s+(\d+)", output)
        return int(match.group(2)) if match else 0

    def get_subscribers(self, ssh_client):
        stdin, stdout, stderr = ssh_client.exec_command("show subscribers | display json")
        output = stdout.read().decode('utf-8', errors='replace')
        data = json.loads(output)
        logins = []
        for block in data.get("subscribers-information", []):
            for subscriber in block.get("subscriber", []):
                user_data = subscriber.get("user-name", [{}])[0].get("data")
                if user_data:
                    logins.append(user_data)
        return logins

    def save_subscriber_snapshot(self, login_list):
        SubscriberSnapshot.objects.create(logins=login_list)

    def analyze_disconnections(self, disappeared):
        onus = Onu.objects.filter(pppoe_user__in=disappeared)
        if not onus.exists():
            log_to_db('system', 'INFO', "Nenhuma ONU encontrada para esses logins.", None, None)
            return

        estrutura = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        for onu in onus:
            olt_key = str(onu.olt) if onu.olt else "SEM_OLT"
            slot_key = onu.slot_number
            pon_key = onu.pon_number
            cto_val = onu.cto if onu.cto else "SEM_CTO"
            estrutura[olt_key][slot_key][pon_key][cto_val].append(onu.pppoe_user)

        hierarchy_data = self.to_normal_dict(estrutura)
        msg_final = self.generate_detailed_message(hierarchy_data)

        Alert.objects.create(
            problem_type="DESCONEXOES",
            detail="Análise Hierárquica",
            message=msg_final,
            hierarchy_data=hierarchy_data
        )
        log_to_db('network', 'WARNING', msg_final, None, hierarchy_data)

    def check_total_failures(self, hierarchy_data):
        # (se ainda usar em outro lugar)
        for olt, slots in hierarchy_data.items():
            for slot, pons in slots.items():
                for pon, ctos in pons.items():
                    for cto, users_down in ctos.items():
                        total_clients = Onu.objects.filter(
                            olt__name=olt,
                            slot_number=slot,
                            pon_number=pon,
                            cto=cto
                        ).count()
                        down_count = len(users_down)
                        if down_count > 0 and down_count == total_clients:
                            log_to_db(
                                'network', 'CTO_DOWN',
                                f"CTO {cto} totalmente OFFLINE ({down_count}/{total_clients})",
                                detail="Queda total de CTO",
                                hierarchy_data={'olt': olt, 'slot': slot, 'pon': pon, 'cto': cto}
                            )
                        elif down_count == 0 and total_clients > 0:
                            log_to_db(
                                'network', 'CTO_UP',
                                f"CTO {cto} recuperada com {total_clients} clientes",
                                detail="Recuperação total de CTO",
                                hierarchy_data={'olt': olt, 'slot': slot, 'pon': pon, 'cto': cto}
                            )

    def generate_detailed_message(self, hierarchy):
        messages = []
        for olt, slots in hierarchy.items():
            for slot, pons in slots.items():
                for pon, cto_dict in pons.items():
                    total_quedas = sum(len(users) for users in cto_dict.values())
                    header = f"{total_quedas} quedas em OLT {olt}, SLOT {slot}, PON {pon}"
                    detalhes = [
                        f"CTO {cto}: {len(users)} quedas – Usuários: {', '.join(users)}"
                        for cto, users in cto_dict.items()
                    ]
                    messages.append(header + "\n" + "\n".join(detalhes))
        return "\n\n".join(messages) if messages else "Nenhuma queda hierárquica detectada."

    def build_cto_map(self, logins):
        mapa = defaultdict(list)
        for onu in Onu.objects.filter(pppoe_user__in=logins):
            mapa[onu.cto].append(onu.pppoe_user)
        return mapa

    def to_normal_dict(self, d):
        if isinstance(d, defaultdict):
            return {k: self.to_normal_dict(v) for k, v in d.items()}
        elif isinstance(d, dict):
            return {k: self.to_normal_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [self.to_normal_dict(x) for x in d]
        else:
            return d
