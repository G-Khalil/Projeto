from django.urls import path
from . import views

urlpatterns = [
    path('hoje/', views.lista_presenca_hoje, name='lista_presenca_hoje'),
    path('relatorio/exportar/', views.exportar_relatorio_mensal, name='exportar_relatorio'),
    path('relatorio/diario/exportar/', views.exportar_relatorio_diario, name='exportar_relatorio_diario'),
    path('registrar/', views.registrar_entrada_saida, name='registrar_entrada_saida'),
    path('api/registrar-acesso/', views.registrar_acesso_ajax, name='registrar_acesso_ajax'),
    path('api/recognize-register/', views.recognize_and_register_ajax, name='recognize_and_register_ajax'),
    path('api/recognize-register-auto/', views.recognize_and_register_auto, name='recognize_and_register_auto'),
    path('lista-funcionarios/', views.lista_funcionarios_entrada_saida, name='lista_funcionarios_entrada_saida'),
]
