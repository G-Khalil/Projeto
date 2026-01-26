from datetime import datetime, timedelta
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
import base64
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from acessos.models import AcessoObra
from empresas.models import Empresa
from funcionarios.models import Funcionario

def lista_presenca_hoje(request):
    hoje = timezone.now().date()
    # Separar por empresa
    empresas = Empresa.objects.all().order_by('nome')
    dados_empresas = []
    
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

def exportar_relatorio_diario(request):
    data_str = request.GET.get('data', timezone.now().strftime('%Y-%m-%d'))
    data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    
    wb = Workbook()
    ws = wb.active
    ws.title = f"Presenca_{data_str}"
    
    # Estilos (Mantendo seu padrão)
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

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="presenca_{data_str}.xlsx"'
    wb.save(response)
    return response

def lista_funcionarios_entrada_saida(request):
    hoje = timezone.now().date()
    # Agrupar por empresa
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
