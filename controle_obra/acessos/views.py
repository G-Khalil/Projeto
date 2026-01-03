from datetime import datetime, timedelta

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
import base64

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from acessos.models import AcessoObra
from empresas.models import Empresa
from funcionarios.models import Funcionario


def lista_presenca_hoje(request):
    """
    Tela de presença de hoje.
    Mostra os acessos do dia atual.
    """
    hoje = timezone.now().date()
    acessos = (
        AcessoObra.objects
        .filter(data=hoje)
        .select_related('funcionario', 'funcionario__empresa')
        .order_by('funcionario__nome')
    )

    context = {
        'acessos': acessos,
        'data': hoje,
    }
    return render(request, 'acessos/lista_presenca_hoje.html', context)


def exportar_relatorio_mensal(request):
    """
    Relatório mensal de presença em Excel.
    Presença = dias em que existe AcessoObra.
    Ausência = dias do mês - dias presentes.
    """
    hoje = timezone.now()
    mes = int(request.GET.get('mes', hoje.month))
    ano = int(request.GET.get('ano', hoje.year))

    # datas do mês
    primeiro_dia = datetime(ano, mes, 1).date()
    if mes == 12:
        ultimo_dia = datetime(ano + 1, 1, 1).date() - timedelta(days=1)
    else:
        ultimo_dia = datetime(ano, mes + 1, 1).date() - timedelta(days=1)
    total_dias_mes = (ultimo_dia - primeiro_dia).days + 1

    # ==== workbook ====
    wb = Workbook()
    ws = wb.active
    ws.title = f"Presenca_{mes:02d}_{ano}"

    # estilos
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)

    subheader_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    subheader_font = Font(bold=True, color="000000", size=10)

    total_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    total_font = Font(bold=True, color="000000", size=10)

    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin'),
    )

    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    # título
    ws.merge_cells('A1:F1')
    title = ws['A1']
    title.value = f"RELATORIO DE PRESENCA - {mes:02d}/{ano}"
    title.font = Font(bold=True, size=14, color="FFFFFF")
    title.fill = PatternFill(start_color="203864", end_color="203864", fill_type="solid")
    title.alignment = center_align
    ws.row_dimensions[1].height = 25

    # cabeçalho funcionários
    headers = ["Funcionário", "Empresa", "Dias Presentes", "Dias Ausentes", "Total de Dias", "Percentual"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=3, column=col)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = border
    ws.row_dimensions[3].height = 20

    # linhas por funcionário
    funcionarios = Funcionario.objects.all().order_by('nome')

    row = 4
    total_presentes_geral = 0
    total_ausentes_geral = 0

    for funcionario in funcionarios:
        acessos_func = AcessoObra.objects.filter(
            funcionario=funcionario,
            data__gte=primeiro_dia,
            data__lte=ultimo_dia,
        )

        # dias com registro = presente
        presentes = (
            acessos_func
            .values('data')
            .distinct()
            .count()
        )
        ausentes = total_dias_mes - presentes
        if ausentes < 0:
            ausentes = 0

        total = presentes + ausentes if presentes + ausentes > 0 else 1
        percentual = (presentes / total) * 100 if total > 0 else 0

        total_presentes_geral += presentes
        total_ausentes_geral += ausentes

        ws.cell(row=row, column=1).value = funcionario.nome
        ws.cell(row=row, column=2).value = (
            funcionario.empresa.nome if getattr(funcionario, "empresa", None) else "N/A"
        )
        ws.cell(row=row, column=3).value = presentes
        ws.cell(row=row, column=4).value = ausentes
        ws.cell(row=row, column=5).value = total
        ws.cell(row=row, column=6).value = f"{percentual:.1f}%"

        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.border = border
            cell.alignment = center_align if col >= 3 else left_align

        row += 1

    # total geral
    ws.cell(row=row, column=1).value = "TOTAL GERAL"
    ws.cell(row=row, column=1).font = total_font
    ws.cell(row=row, column=1).fill = total_fill

    ws.cell(row=row, column=3).value = total_presentes_geral
    ws.cell(row=row, column=3).font = total_font
    ws.cell(row=row, column=3).fill = total_fill

    ws.cell(row=row, column=4).value = total_ausentes_geral
    ws.cell(row=row, column=4).font = total_font
    ws.cell(row=row, column=4).fill = total_fill

    total_geral = total_presentes_geral + total_ausentes_geral
    ws.cell(row=row, column=5).value = total_geral
    ws.cell(row=row, column=5).font = total_font
    ws.cell(row=row, column=5).fill = total_fill

    percentual_geral = (total_presentes_geral / total_geral * 100) if total_geral > 0 else 0
    ws.cell(row=row, column=6).value = f"{percentual_geral:.1f}%"
    ws.cell(row=row, column=6).font = total_font
    ws.cell(row=row, column=6).fill = total_fill

    for col in range(1, 7):
        cell = ws.cell(row=row, column=col)
        cell.border = border
        cell.alignment = center_align

    # ===== resumo por empresa =====
    row += 3
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    empresa_title = ws.cell(row=row, column=1)
    empresa_title.value = "RESUMO POR EMPRESA"
    empresa_title.font = Font(bold=True, size=12, color="FFFFFF")
    empresa_title.fill = PatternFill(start_color="203864", end_color="203864", fill_type="solid")
    empresa_title.alignment = center_align

    row += 1
    empresa_headers = ["Empresa", "Funcionários", "Dias Presentes", "Dias Ausentes", "Total", "Taxa"]
    for col, header in enumerate(empresa_headers, 1):
        cell = ws.cell(row=row, column=col)
        cell.value = header
        cell.font = subheader_font
        cell.fill = subheader_fill
        cell.alignment = center_align
        cell.border = border

    row += 1
    empresas = Empresa.objects.all().order_by('nome')

    for empresa in empresas:
        funcs_empresa = Funcionario.objects.filter(empresa=empresa)

        presentes_emp = 0
        ausentes_emp = 0

        for func in funcs_empresa:
            acessos = AcessoObra.objects.filter(
                funcionario=func,
                data__gte=primeiro_dia,
                data__lte=ultimo_dia,
            )
            pres_dias = acessos.values('data').distinct().count()
            presentes_emp += pres_dias
            ausentes_emp += max(total_dias_mes - pres_dias, 0)

        total_emp = presentes_emp + ausentes_emp if presentes_emp + ausentes_emp > 0 else 1
        taxa_emp = (presentes_emp / total_emp) * 100 if total_emp > 0 else 0

        ws.cell(row=row, column=1).value = empresa.nome
        ws.cell(row=row, column=2).value = funcs_empresa.count()
        ws.cell(row=row, column=3).value = presentes_emp
        ws.cell(row=row, column=4).value = ausentes_emp
        ws.cell(row=row, column=5).value = total_emp
        ws.cell(row=row, column=6).value = f"{taxa_emp:.1f}%"

        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.border = border
            cell.alignment = center_align if col > 1 else left_align

        row += 1

    # largura colunas
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 22
    ws.column_dimensions['C'].width = 16
    ws.column_dimensions['D'].width = 16
    ws.column_dimensions['E'].width = 16
    ws.column_dimensions['F'].width = 16

    # response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="relatorio_presenca_{mes:02d}_{ano}.xlsx"'
    wb.save(response)
    return response

# ============ NOVA VIEW: ENTRADA/SAÍDA COM RECONHECIMENTO FACIAL ============

def registrar_entrada_saida(request):
    """
    Página dedicada para registro de entrada/saída com reconhecimento facial.
    Porteiro usa this, pane para detectar rosto e registrar hora automaticamente.
    """
    hoje = timezone.now().date()
    
    # Últimos acessos do dia (para mostrar na tela)
    acessos_hoje = (
        AcessoObra.objects
        .filter(data=hoje)
        .select_related('funcionario', 'funcionario__empresa')
        .order_by('-id')[:10]  # Últimos 10 registros
    )
    
    # Todos os funcionários para reconhecimento facial
    funcionarios = Funcionario.objects.all().order_by('nome')
    
    context = {
        'acessos_hoje': acessos_hoje,
        'funcionarios': funcionarios,
        'data': hoje,
    }
    
    return render(request, 'acessos/registrar_entrada_saida.html', context)


def registrar_acesso_ajax(request):
    """
    API AJAX para registrar entrada/saída após reconhecimento facial.
    Recebe: funcionario_id, tipo (entrada/saida)
    Retorna: JSON com sucesso/erro e dados do acesso registrado
    """
    import json
    
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=400)
    
    try:
        data = json.loads(request.body)
        funcionario_id = data.get('funcionario_id')
        tipo = data.get('tipo')  # 'entrada' ou 'saida'
        
        funcionario = Funcionario.objects.get(id=funcionario_id)
        hoje = timezone.now().date()
        agora = timezone.now().time()
        
        # Buscar ou criar acesso de hoje
        acesso, criado = AcessoObra.objects.get_or_create(
            funcionario=funcionario,
            data=hoje
        )
        
        if tipo == 'entrada':
            acesso.hora_entrada = agora
            mensagem = f"✅ Entrada registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        elif tipo == 'saida':
            acesso.hora_saida = agora
            mensagem = f"✅ Saída registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        else:
            return JsonResponse({'erro': 'Tipo inválido'}, status=400)
        
        acesso.save()
        
        return JsonResponse({
            'sucesso': True,
            'mensagem': mensagem,
            'funcionario': funcionario.nome,
            'empresa': funcionario.empresa.nome if funcionario.empresa else 'N/A',
            'tipo': tipo,
            'hora': agora.strftime('%H:%M:%S'),
        })
        
    except Funcionario.DoesNotExist:
        return JsonResponse({'erro': 'Funcionário não reconhecido'}, status=404)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


def recognize_and_register_ajax(request):
    """
    Recebe imagem (base64) do cliente, compara com encoding armazenado em
    `Funcionario.facial_data` usando `face_recognition` e registra entrada/saída.
    """
    import json
    from PIL import Image
    from io import BytesIO

    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=400)

    try:
        data = json.loads(request.body)
        funcionario_id = data.get('funcionario_id')
        tipo = data.get('tipo')
        imagem = data.get('imagem')

        if not funcionario_id or not tipo or not imagem:
            return JsonResponse({'erro': 'Dados incompletos'}, status=400)

        funcionario = Funcionario.objects.get(id=funcionario_id)

        facial_data = funcionario.facial_data
        if not facial_data:
            return JsonResponse({'erro': 'Funcionário não possui dados faciais'}, status=400)

        try:
            if isinstance(facial_data, str):
                facial_json = json.loads(facial_data)
            else:
                facial_json = facial_data
            stored_encoding = facial_json.get('encoding')
        except Exception:
            stored_encoding = None

        if not stored_encoding:
            return JsonResponse({'erro': 'Nenhum encoding facial disponível para este funcionário'}, status=400)

        # decodificar imagem enviada
        if ',' in imagem:
            _, imagem = imagem.split(',', 1)
        img_bytes = base64.b64decode(imagem)
        pil_img = Image.open(BytesIO(img_bytes)).convert('RGB')

        import numpy as np
        import face_recognition

        img_array = np.array(pil_img)
        encodings = face_recognition.face_encodings(img_array)
        if not encodings:
            return JsonResponse({'erro': 'Nenhum rosto detectado na imagem'}, status=400)

        captured_encoding = encodings[0]
        stored_np = np.array(stored_encoding)
        matches = face_recognition.compare_faces([stored_np], captured_encoding, tolerance=0.5)
        if not matches or not matches[0]:
            return JsonResponse({'erro': 'Reconhecimento facial falhou'}, status=403)

        # registrar acesso
        hoje = timezone.now().date()
        agora = timezone.now().time()

        acesso, criado = AcessoObra.objects.get_or_create(funcionario=funcionario, data=hoje)
        if tipo == 'entrada':
            if acesso.hora_entrada:
                return JsonResponse({'erro': 'Entrada já registrada'}, status=409)
            acesso.hora_entrada = agora
            mensagem = f"✅ Entrada registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        elif tipo == 'saida':
            if acesso.hora_saida:
                return JsonResponse({'erro': 'Saída já registrada'}, status=409)
            acesso.hora_saida = agora
            mensagem = f"✅ Saída registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        else:
            return JsonResponse({'erro': 'Tipo inválido'}, status=400)

        acesso.save()

        return JsonResponse({'sucesso': True, 'mensagem': mensagem, 'funcionario': funcionario.nome, 'funcionario_id': funcionario.id, 'tipo': tipo, 'hora': agora.strftime('%H:%M:%S')})

    except Funcionario.DoesNotExist:
        return JsonResponse({'erro': 'Funcionário não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


def recognize_and_register_auto(request):
    """
    Recebe imagem (base64) do cliente, compara com todos os encodings
    armazenados em `Funcionario.facial_data` e registra entrada/saída
    automaticamente ao encontrar melhor correspondência abaixo do
    threshold definido.
    """
    import json
    from PIL import Image
    from io import BytesIO

    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido'}, status=400)

    try:
        data = json.loads(request.body)
        tipo = data.get('tipo')
        imagem = data.get('imagem')

        if not tipo or not imagem:
            return JsonResponse({'erro': 'Dados incompletos'}, status=400)

        # decodificar imagem enviada
        if ',' in imagem:
            _, imagem = imagem.split(',', 1)
        img_bytes = base64.b64decode(imagem)
        pil_img = Image.open(BytesIO(img_bytes)).convert('RGB')

        import numpy as np
        import face_recognition

        img_array = np.array(pil_img)
        encodings = face_recognition.face_encodings(img_array)
        if not encodings:
            return JsonResponse({'erro': 'Nenhum rosto detectado na imagem'}, status=400)

        captured_encoding = encodings[0]

        # Iterar por funcionários que têm facial_data
        candidatos = Funcionario.objects.exclude(facial_data__isnull=True).exclude(facial_data__exact='')
        best_match = None
        best_distance = None

        for func in candidatos:
            facial_data = func.facial_data
            try:
                if isinstance(facial_data, str):
                    facial_json = json.loads(facial_data)
                else:
                    facial_json = facial_data
                stored_encoding = facial_json.get('encoding')
            except Exception:
                stored_encoding = None

            if not stored_encoding:
                continue

            stored_np = np.array(stored_encoding)
            # calcular distância
            dist = face_recognition.face_distance([stored_np], captured_encoding)[0]
            if best_distance is None or dist < best_distance:
                best_distance = dist
                best_match = func

        # threshold ajustável
        THRESHOLD = 0.55
        if best_match is None or best_distance is None or best_distance > THRESHOLD:
            return JsonResponse({'erro': 'Nenhuma correspondência confiável encontrada', 'distance': best_distance}, status=404)

        funcionario = best_match

        # registrar acesso
        hoje = timezone.now().date()
        agora = timezone.now().time()

        acesso, criado = AcessoObra.objects.get_or_create(funcionario=funcionario, data=hoje)
        if tipo == 'entrada':
            if acesso.hora_entrada:
                return JsonResponse({'erro': 'Entrada já registrada'}, status=409)
            acesso.hora_entrada = agora
            mensagem = f"✅ Entrada registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        elif tipo == 'saida':
            if acesso.hora_saida:
                return JsonResponse({'erro': 'Saída já registrada'}, status=409)
            acesso.hora_saida = agora
            mensagem = f"✅ Saída registrada para {funcionario.nome} às {agora.strftime('%H:%M')}"
        else:
            return JsonResponse({'erro': 'Tipo inválido'}, status=400)

        acesso.save()

        return JsonResponse({'sucesso': True, 'mensagem': mensagem, 'funcionario': funcionario.nome, 'funcionario_id': funcionario.id, 'tipo': tipo, 'hora': agora.strftime('%H:%M:%S'), 'distance': best_distance})

    except Exception as e:
        return JsonResponse({'erro': str(e)}, status=500)


def lista_funcionarios_entrada_saida(request):
    """
    Lista de funcionarios com status de entrada/saida.
    - Vermelho: Nao chegou na obra
    - Verde: Ja registrou entrada
    - Cinza: Ja registrou saida
    Requer reconhecimento facial para registrar entrada/saida.
    """
    hoje = timezone.now().date()
    
    # Buscar todos os funcionarios
    funcionarios = Funcionario.objects.all().order_by('nome')
    
    # Preparar lista com status
    funcionarios_com_status = []
    
    for func in funcionarios:
        # Buscar acesso de hoje para este funcionario
        acesso_hoje = AcessoObra.objects.filter(
            funcionario=func,
            data=hoje
        ).first()
        
        # Determinar status
        if acesso_hoje is None:
            status = 'nao-chegou'  # Vermelho (hyphen for CSS/JS)
            status_display = 'Nao chegou'
            hora_entrada = None
            hora_saida = None
        elif acesso_hoje.hora_saida:
            status = 'saida'  # Cinza
            status_display = 'Saida registrada'
            hora_entrada = acesso_hoje.hora_entrada
            hora_saida = acesso_hoje.hora_saida
        else:
            status = 'entrada'  # Verde
            status_display = 'Entrada registrada'
            hora_entrada = acesso_hoje.hora_entrada
            hora_saida = None
        
        funcionarios_com_status.append({
            'id': func.id,
            'nome': func.nome,
            'empresa': func.empresa.nome if func.empresa else 'N/A',
            'status': status,
            'status_display': status_display,
            'hora_entrada': hora_entrada,
            'hora_saida': hora_saida,
            'tem_foto': bool(func.foto),
        })
    
    context = {
        'funcionarios': funcionarios_com_status,
        'data': hoje,
    }
    
    return render(request, 'acessos/lista_funcionarios_entrada_saida.html', context)


