#SentinelaApolo/upload_csv/views.py
import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Onu, Olt
from .forms import CsvUploadForm
from django.contrib.auth.decorators import login_required

@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, "Por favor, envie um arquivo CSV válido.")
                return redirect('upload_csv')

            try:
                # Decodificar o arquivo CSV
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)

                # Validar colunas obrigatórias
                required_columns = [
                    'ONU Status',
                    'Device Name',
                    'Slot Number',
                    'PON Number',
                    'Physical Address'
                ]
                if not all(col in reader.fieldnames for col in required_columns):
                    messages.error(request, f"Colunas obrigatórias não encontradas: {', '.join(required_columns)}.")
                    return redirect('upload_csv')

                # Extrair o nome da OLT do nome do arquivo
                olt_name = csv_file.name.split('.')[0]  # Ex.: "OLT01.csv" -> "OLT01"
                olt, _ = Olt.objects.get_or_create(name=olt_name)

                # Função para separar partes do Device Name
                def parse_device_name(value):
                    if not value or value.strip() == '':
                        return ('999', '999', '999')
                    parts = [p.strip() for p in str(value).split('-')]
                    cto = parts[0] if len(parts) > 0 else '999'
                    pppoe_user = parts[1] if len(parts) > 1 else '999'
                    user_code = parts[2] if len(parts) > 2 else '999'
                    return (cto, pppoe_user, user_code)

                # Processar cada linha do CSV
                for row in reader:
                    device_name = row.get("Device Name", "").strip() if row.get("Device Name") else '999'
                    slot_number = row.get("Slot Number", "").strip() if row.get("Slot Number") else '999'
                    pon_number = row.get("PON Number", "").strip() if row.get("PON Number") else '999'
                    physical_address = row.get("Physical Address", "").strip() if row.get("Physical Address") else '999'
                    onu_status = row.get("ONU Status", "").strip() if row.get("ONU Status") else 'unknown'

                    # Converter valores numéricos
                    try:
                        slot_number = int(slot_number) if slot_number and slot_number != '999' else 999
                        pon_number = int(pon_number) if pon_number and pon_number != '999' else 999
                    except ValueError:
                        messages.warning(request, f"Valores inválidos para Slot/PON: {slot_number}/{pon_number}. Usando padrão 999.")
                        slot_number = 999
                        pon_number = 999

                    # Separar partes do Device Name
                    cto, pppoe_user, user_code = parse_device_name(device_name)

                    # Criar ou atualizar o registro da ONU
                    Onu.objects.update_or_create(
                        device_name=device_name,
                        olt=olt,
                        defaults={
                            "slot_number": slot_number,
                            "pon_number": pon_number,
                            "physical_address": physical_address,
                            "cto": cto,
                            "pppoe_user": pppoe_user,
                            "user_code": user_code,
                            "onu_status": onu_status,
                        }
                    )

                messages.success(request, "Dados do CSV foram carregados com sucesso!")
                return redirect('upload_csv')

            except Exception as e:
                messages.error(request, f"Erro ao processar o arquivo CSV: {str(e)}")
                return redirect('upload_csv')

    else:
        form = CsvUploadForm()

    return render(request, 'upload_csv.html', {'form': form})