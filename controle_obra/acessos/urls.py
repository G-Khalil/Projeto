from django.urls import path
from . import views

urlpatterns = [
    path('hoje/', views.lista_presenca_hoje, name='lista_presenca_hoje'),
    path('relatorio/exportar/', views.exportar_excel_mensal, name='exportar_relatorio'),
    path('relatorio/diario/exportar/', views.exportar_excel_diario, name='exportar_relatorio_diario'),
    path('registrar/', views.registrar_entrada_saida, name='registrar_entrada_saida'),
    path('api/registrar-acesso/', views.registrar_acesso_ajax, name='registrar_acesso_ajax'),
    path('api/reconhecer/', views.reconhecer_and_register_ajax, name='reconhecer_and_register_ajax'),
    path('api/reconhecer-auto/', views.reconhecer_and_register_auto, name='reconhecer_and_register_auto'),
    path('lista-funcionarios/', views.lista_funcionarios_entrada_saida, name='lista_funcionarios_entrada_saida'),
    path('relatorio/mensal/exportar/', views.exportar_excel_mensal, name='exportar_excel_mensal'),
    path('relatorio/diario/exportar/', views.exportar_excel_diario, name='exportar_excel_diario'),
]
