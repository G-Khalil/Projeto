from datetime import datetime, timedelta

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

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


from django.http import JsonResponse

