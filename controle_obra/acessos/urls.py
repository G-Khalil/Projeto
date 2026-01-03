from django.urls import path
from . import views

urlpatterns = [
    path('hoje/', views.lista_presenca_hoje, name='lista_presenca_hoje'),
    path('relatorio/exportar/', views.exportar_relatorio_mensal, name='exportar_relatorio'),
        path('registrar/', views.lista_presenca_hoje, name='registrar_entrada_saida'),
    path('api/registrar-acesso/', views.registrar_acesso_ajax, name='registrar_acesso_ajax'),
    path('lista-funcionarios/', views.lista_funcionarios_entrada_saida, name='lista_funcionarios_entrada_saida')
]




