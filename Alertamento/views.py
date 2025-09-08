# #D:/SentinelaApolo/Alertamento/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Incidente
from .forms import IncidenteForm 
from django.http import JsonResponse
from django.shortcuts import render

@login_required
def incident_list(request):
    """
    Lista todos os incidentes, ordenados pelo mais recente.
    """
    incidents = Incidente.objects.order_by('-timestamp')
    return render(request, 'alertamento/incident_list.html', {
        'incidents': incidents
    })

@login_required
def incident_detail(request, pk):
    """
    Mostra detalhes de um único incidente.
    """
    incident = get_object_or_404(Incidente, pk=pk)
    return render(request, 'alertamento/incident_detail.html', {
        'incident': incident
    })

@login_required
def incident_create(request):
    """
    Formulário para criar um novo incidente (por exemplo, disparado manualmente).
    """
    if request.method == 'POST':
        form = IncidenteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('alertamento:incident_list')
    else:
        form = IncidenteForm()
    return render(request, 'alertamento/incident_form.html', {
        'form': form
    })


@login_required
def get_incidentes(request):
    """
    API simples que retorna todos os incidentes em JSON.
    """
    qs = Incidente.objects.order_by('-timestamp')
    data = [
        {
            'id': inc.id,
            'tipo': inc.tipo,
            'nivel': inc.nivel,
            'mensagem': inc.mensagem,
            'detalhes': inc.detalhes,
            'timestamp': inc.timestamp.isoformat(),
        }
        for inc in qs
    ]
    return JsonResponse(data, safe=False)