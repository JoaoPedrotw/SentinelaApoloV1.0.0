# D:/SentinelaApolo/Monitoramento/views.py

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import threading
import subprocess

from django.utils import timezone
from django.db import ProgrammingError
from django.contrib.auth.decorators import login_required

from Monitoramento.models import Alert, SystemLog, NetworkAlert
from Alertamento.models import Incidente


def run_monitoring():
    """
    Função interna (não é view) que dispara o comando de monitoramento em background.
    """
    try:
        subprocess.run(
            ['python', 'manage.py', 'monitorador_de_rede'],
            cwd=settings.BASE_DIR,
            check=True
        )
    except Exception as e:
        # Apenas um print aqui, o log de erro vai para o console/arquivo de logs do Gunicorn
        print(f"Erro ao executar o monitoramento: {e}")

@login_required
@csrf_exempt
def iniciar_monitoramento(request):
    """
    View que é chamada via POST para iniciar o monitoramento em background.
    """
    if request.method == 'POST':
        try:
            threading.Thread(target=run_monitoring, daemon=True).start()
            return JsonResponse({'status': 'success', 'message': 'Monitoramento iniciado com sucesso.'})
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': f'Erro ao iniciar o monitoramento: {e}'},
                status=500
            )
    # GET cai aqui e exibe a página de monitoramento
    return render(request, 'monitoramento.html')

@login_required
def get_logs(request):
    """
    Retorna os alertas detalhados (modelo Alert) em JSON.
    """
    try:
        logs = Alert.objects.all().order_by('-timestamp')[:10]
        data = [
            {
                'timestamp': timezone.localtime(l.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                'message': l.message,
                'hierarchy': l.hierarchy_data
            }
            for l in logs
        ]
        return JsonResponse(data, safe=False)
    except ProgrammingError as e:
        return JsonResponse(
            {'status': 'error', 'message': f'Erro ao acessar o banco de dados: {e}'},
            status=500
        )

@login_required
def get_system_logs(request):
    """
    Retorna os logs de sistema (modelo SystemLog) em JSON.
    """
    try:
        logs = SystemLog.objects.all().order_by('-timestamp')[:10]
        data = [
            {
                'timestamp': timezone.localtime(l.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                'level': l.level,
                'message': l.message
            }
            for l in logs
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': f'Erro ao buscar logs de sistema: {e}'},
            status=500
        )

@login_required
def get_network_alerts(request):
    """
    Retorna os avisos de monitoramento de rede (modelo NetworkAlert) em JSON.
    """
    try:
        alerts = NetworkAlert.objects.all().order_by('-timestamp')[:10]
        data = [
            {
                'timestamp': timezone.localtime(a.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                'problem_type': a.problem_type,
                'message': a.message,
                'detail': a.detail,
                'hierarchy_data': a.hierarchy_data
            }
            for a in alerts
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse(
            {'status': 'error', 'message': f'Erro ao buscar avisos de monitoramento: {e}'},
            status=500
        )

@login_required
def home_view(request):
    """
    Rende a página principal do monitoramento.
    """
    return render(request, 'monitoramento.html')

# === NOVO ENDPOINT PARA RECUPERAÇÕES ===
@login_required
def get_recoveries(request):
    """
    Retorna os últimos 10 incidentes de RECOVERY em JSON,
    para o front-end exibir somente os retornos de conexão
    dos usuários que tiveram queda crítica.
    """
    if request.method == 'GET':
        recs = (
            Incidente.objects
            .filter(tipo='RECOVERY')
            .order_by('-timestamp')[:10]
        )
        data = [
            {
                'id': inc.id,
                'timestamp': timezone.localtime(inc.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                'mensagem': inc.mensagem,
                'detalhes': inc.detalhes,
            }
            for inc in recs
        ]
        return JsonResponse(data, safe=False)
    return JsonResponse({'status':'error','message':'Método não permitido.'}, status=405)
