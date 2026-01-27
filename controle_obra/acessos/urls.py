from django.urls import path
from . import views

urlpatterns = [
    path('hoje/', views.lista_presenca_hoje, name='lista_presenca_hoje'),
    path('lista-funcionarios/', views.lista_funcionarios_entrada_saida, name='lista_funcionarios_entrada_saida'),
    path('relatorio/mensal/exportar/', views.exportar_excel_mensal, name='exportar_excel_mensal'),
    path('relatorio/diario/exportar/', views.exportar_excel_diario, name='exportar_excel_diario'),
]
