from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
import base64
import json
from PIL import Image
from io import BytesIO
import numpy as np
import face_recognition
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from acessos.models import AcessoObra
from empresas.models import Empresa
from funcionarios.models import Funcionario

def lista_presenca_hoje(request):
    """
    Tela de presença de hoje agrupada por empresa.
    """
    data_str = request.GET.get('data', timezone.now().strftime('%Y-%m-%d'))
    hoje = datetime.strptime(data_str, '%Y-%m-%d').date()
    dados_empresas = []
    empresas = Empresa.objects.all().order_by('nome')
         
    for empresa in empresas:

    
        funcionarios = Funcionario.objects.filter(empresa=empresa).order_by('nome')
        acessos_empresa = []
        for func in funcionarios:
            acesso = AcessoObra.objects.filter(funcionario=func, data=hoje).first()
            acessos_empresa.append({
                'funcionario': func,
                'acesso': acesso
            })
        
        if acessos_empresa:
            dados_empresas.append({
                'empresa': empresa,
                'dados': acessos_empresa
            })

    context = {
        'dados_empresas': dados_empresas,
        'data': hoje,
    }
    return render(request, 'acessos/lista_presenca_hoje.html', context)

def exportar_relatorio_mensal(request):
    """
    Relatório mensal de presença em Excel (Restaurado).
    """
    hoje = timezone.now()
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))
    
    primeiro_dia = datetime(ano, mes, 1).date()
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1).date() - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1).date() - timedelta(days=1)
    total_dias_mes = (ultimo_dia - primeiro_dia).days + 1

    wb = Workbook()
    ws = wb.active
    ws.title = f"Presenca_{mes:02d}_{ano}"
    
    # Estilos
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    center_align = Alignment(horizontal="center", vertical="center")
    
    ws.merge_cells('A1:F1')
    title = ws['A1']
    title.value = f"RELATORIO DE PRESENCA - {mes:02d}/{ano}"
    title.font = Font(bold=True, size=14, color="FFFFFF")
    title.fill = PatternFill(start_color="203864", end_color="203864", fill_type="solid")
    title.alignment = center_align
    
    headers = ["Funcionário", "Empresa", "Dias Presentes", "Dias Ausentes", "Total de Dias", "Percentual"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border

    row = 4
    funcionarios = Funcionario.objects.all().order_by('nome')
    for funcionario in funcionarios:
        acessos_func = AcessoObra.objects.filter(funcionario=funcionario, data__gte=primeiro_dia, data__lte=ultimo_dia)
        presentes = acessos_func.values('data').distinct().count()
        ausentes = max(0, total_dias_mes - presentes)
        total = total_dias_mes
        percentual = (presentes / total) * 100 if total > 0 else 0
        
        ws.cell(row=row, column=1, value=funcionario.nome).border = border
        ws.cell(row=row, column=2, value=funcionario.empresa.nome if funcionario.empresa else "N/A").border = border
        ws.cell(row=row, column=3, value=presentes).border = border
        ws.cell(row=row, column=4, value=ausentes).border = border
        ws.cell(row=row, column=5, value=total).border = border
        ws.cell(row=row, column=6, value=f"{percentual:.1f}%").border = border
        row += 1

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="relatorio_presenca_{mes:02d}_{ano}.xlsx"'
    wb.save(response)
    return response

def exportar_relatorio_diario(request):
    """
    Novo relatório diário agrupado por empresa.
    """
    data_str = request.GET.get('data', timezone.now().strftime('%Y-%m-%d'))
    data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    
    wb = Workbook()
    ws = wb.active
    ws.title = f"Presenca_{data_str}"
    
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    
    ws.merge_cells('A1:E1')
    ws['A1'] = f"RELATÓRIO DE PRESENÇA - {data_obj.strftime('%d/%m/%Y')}"
    ws['A1'].font = Font(bold=True, size=14)
    ws['A1'].alignment = Alignment(horizontal="center")
    
    row = 3
    empresas = Empresa.objects.all().order_by('nome')
    
    for empresa in empresas:
        ws.cell(row=row, column=1, value=empresa.nome).font = Font(bold=True)
        ws.cell(row=row, column=1).fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        row += 1
        
        headers = ["Funcionário", "Empresa", "Entrada", "Saída", "Status"]
        for col, text in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=text)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
        row += 1
        
        funcs = Funcionario.objects.filter(empresa=empresa).order_by('nome')
        for f in funcs:
            acesso = AcessoObra.objects.filter(funcionario=f, data=data_obj).first()
            ws.cell(row=row, column=1, value=f.nome).border = border
            ws.cell(row=row, column=2, value=empresa.nome).border = border
            ws.cell(row=row, column=3, value=acesso.hora_entrada.strftime('%H:%M') if acesso and acesso.hora_entrada else "-").border = border
            ws.cell(row=row, column=4, value=acesso.hora_saida.strftime('%H:%M') if acesso and acesso.hora_saida else "-").border = border
            status = "Não chegou" if not acesso else ("Presente" if not acesso.hora_saida else "Saída registrada")
            ws.cell(row=row, column=5, value=status).border = border
            row += 1
        row += 1

    ws.column_dimensions['A'].width = 30
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="presenca_{data_str}.xlsx"'
    wb.save(response)
    return response

def registrar_entrada_saida(request):
    """
    Página dedicada para registro de entrada/saída com reconhecimento facial (Restaurado).
    """
    hoje = timezone.now().date()
    acessos_hoje = AcessoObra.objects.filter(data=hoje).select_related('funcionario', 'funcionario__empresa').order_by('-id')[:10]
    funcionarios = Funcionario.objects.all().order_by('nome')
    context = {'acessos_hoje': acessos_hoje, 'funcionarios': funcionarios, 'data': hoje}
    return render(request, 'acessos/registrar_entrada_saida.html', context)

def registrar_acesso_ajax(request):
    """
    API AJAX para registrar entrada/saída (Restaurado).
    """
    if request.method != 'POST': return JsonResponse({'erro': 'Método não permitido'}, status=400)
    try:
        data = json.loads(request.body)
        funcionario_id = data.get('funcionario_id')
        tipo = data.get('tipo')
        funcionario = Funcionario.objects.get(id=funcionario_id)
        hoje = timezone.now().date()
        agora = timezone.now().time()
        acesso, criado = AcessoObra.objects.get_or_create(funcionario=funcionario, data=hoje)
        if tipo == 'entrada':
            acesso.hora_entrada = agora
            mensagem = f"✅ Entrada registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        elif tipo == 'saida':
            acesso.hora_saida = agora
            mensagem = f"✅ Saída registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        else: return JsonResponse({'erro': 'Tipo inválido'}, status=400)
        acesso.save()
        return JsonResponse({'sucesso': True, 'mensagem': mensagem, 'funcionario': funcionario.nome, 'tipo': tipo, 'hora': agora.strftime('%H:%M:%S')})
    except Exception as e: return JsonResponse({'erro': str(e)}, status=500)

def recognize_and_register_ajax(request):
    """
    Reconhecimento facial para funcionário específico (Restaurado).
    """
    if request.method != 'POST': return JsonResponse({'erro': 'Método não permitido'}, status=400)
    try:
        data = json.loads(request.body)
        funcionario_id = data.get('funcionario_id')
        tipo = data.get('tipo')
        imagem = data.get('imagem')
        funcionario = Funcionario.objects.get(id=funcionario_id)
        if not funcionario.facial_data: return JsonResponse({'erro': 'Sem dados faciais'}, status=400)
        
        # Processamento de imagem
        if ',' in imagem: _, imagem = imagem.split(',', 1)
        img_bytes = base64.b64decode(imagem)
        pil_img = Image.open(BytesIO(img_bytes)).convert('RGB')
        img_array = np.array(pil_img)
        encodings = face_recognition.face_encodings(img_array)
        if not encodings: return JsonResponse({'erro': 'Nenhum rosto detectado'}, status=400)
        
        facial_json = json.loads(funcionario.facial_data) if isinstance(funcionario.facial_data, str) else funcionario.facial_data
        stored_encoding = np.array(facial_json.get('encoding'))
        matches = face_recognition.compare_faces([stored_encoding], encodings[0], tolerance=0.5)
        if not matches[0]: return JsonResponse({'erro': 'Reconhecimento falhou'}, status=403)
        
        hoje = timezone.now().date()
        agora = timezone.now().time()
        acesso, criado = AcessoObra.objects.get_or_create(funcionario=funcionario, data=hoje)
        if tipo == 'entrada': acesso.hora_entrada = agora
        elif tipo == 'saida': acesso.hora_saida = agora
        acesso.save()
        return JsonResponse({'sucesso': True, 'mensagem': f'Acesso {tipo} registrado!', 'funcionario': funcionario.nome, 'hora': agora.strftime('%H:%M')})
    except Exception as e: return JsonResponse({'erro': str(e)}, status=500)

def recognize_and_register_auto(request):
    """
    Reconhecimento facial automático entre todos os funcionários (Restaurado).
    """
    if request.method != 'POST': return JsonResponse({'erro': 'Método não permitido'}, status=400)
    try:
        data = json.loads(request.body)
        tipo = data.get('tipo')
        imagem = data.get('imagem')
        if ',' in imagem: _, imagem = imagem.split(',', 1)
        img_bytes = base64.b64decode(imagem)
        pil_img = Image.open(BytesIO(img_bytes)).convert('RGB')
        img_array = np.array(pil_img)
        encodings = face_recognition.face_encodings(img_array)
        if not encodings: return JsonResponse({'erro': 'Nenhum rosto detectado'}, status=400)
        
        candidatos = Funcionario.objects.exclude(facial_data__isnull=True).exclude(facial_data__exact='')
        best_match = None
        best_distance = 1.0
        
        for func in candidatos:
            facial_json = json.loads(func.facial_data) if isinstance(func.facial_data, str) else func.facial_data
            stored_encoding = np.array(facial_json.get('encoding'))
            dist = face_recognition.face_distance([stored_encoding], encodings[0])[0]
            if dist < best_distance:
                best_distance = dist
                best_match = func
        
        if best_match and best_distance < 0.55:
            hoje = timezone.now().date()
            agora = timezone.now().time()
            acesso, criado = AcessoObra.objects.get_or_create(funcionario=best_match, data=hoje)
            if tipo == 'entrada': acesso.hora_entrada = agora
            elif tipo == 'saida': acesso.hora_saida = agora
            acesso.save()
            return JsonResponse({'sucesso': True, 'funcionario': best_match.nome, 'tipo': tipo, 'hora': agora.strftime('%H:%M'), 'foto_url': best_match.foto.url if best_match.foto else None})
        return JsonResponse({'error': 'Não reconhecido'}, status=404)
    except Exception as e: return JsonResponse({'erro': str(e)}, status=500)

def lista_funcionarios_entrada_saida(request):
    """
    Lista de funcionários agrupada por empresa com status de entrada/saída.
    """
    hoje = timezone.now().date()
    empresas = Empresa.objects.all().order_by('nome')
    lista_final = []
    
    for empresa in empresas:
        funcionarios = Funcionario.objects.filter(empresa=empresa).order_by('nome')
        funcs_status = []
        for func in funcionarios:
            acesso = AcessoObra.objects.filter(funcionario=func, data=hoje).first()
            status = 'nao-chegou'
            display = 'Não chegou'
            if acesso:
                if acesso.hora_saida:
                    status = 'saida'
                    display = 'Saída registrada'
                else:
                    status = 'entrada'
                    display = 'Entrada registrada'
            
            funcs_status.append({
                'id': func.id,
                'nome': func.nome,
                'status': status,
                'status_display': display,
                'hora_entrada': acesso.hora_entrada if acesso else None,
                'hora_saida': acesso.hora_saida if acesso else None,
                'tem_foto': bool(func.foto),
                'foto_url': func.foto.url if func.foto else None
            })
        if funcs_status:
            lista_final.append({'empresa': empresa.nome, 'funcionarios': funcs_status})

    return render(request, 'acessos/lista_funcionarios_entrada_saida.html', {'empresas_agrupadas': lista_final, 'data': hoje})



def exportar_excel_mensal(request):
        """Exporta relatório de acessos mensal em Excel."""
        mes = int(request.GET.get('mes', timezone.now().month))
        ano = int(request.GET.get('ano', timezone.now().year))

    # Buscar acessos do mês
        acessos = AcessoObra.objects.filter(data__month=mes, data__year=ano).select_related('funcionario')

    # Criar workbook
    wb = Workbook()
    ws = wb.active
    ws.title = f'Acessos {mes:02d}/{ano}'
    ws.append(['Data', 'Funcionário', 'Hora Entrada', 'Hora Saída'])

    for acesso in acessos:
                ws.append([
                                str(acesso.data),
                                acesso.funcionario.nome,
                                str(acesso.hora_entrada) if acesso.hora_entrada else '',
                                str(acesso.hora_saida) if acesso.hora_saida else ''
                            ])

    # Salvar workbook em memória
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="acessos_{mes:02d}_{ano}.xlsx"'
    return response


        def exportar_excel_diario(request):
                """Exporta relatório de acessos do dia atual em Excel."""
                hoje = timezone.now().date()
            acessos = AcessoObra.objects.filter(data=hoje).select_related('funcionario')
    
        wb = Workbook()
        ws = wb.active
    ws.title = f'Acessos {hoje}'
    ws.append(['Data', 'Funcionário', 'Hora Entrada', 'Hora Saída'])
    for acesso in acessos:
                ws.append([str(acesso.data), acesso.funcionario.nome, str(acesso.hora_entrada) if acesso.hora_entrada else '', str(acesso.hora_saida) if acesso.hora_saida else ''])

    output = BytesIO()
        wb.save(output)
        output.seek(0)
    
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="acessos_{hoje}.xlsx"'
    return response

    
    
    









