from django.urls import path
from . import views

urlpatterns = [
    path('hoje/', views.lista_presenca_hoje, name='lista_presenca_hoje'),
    path('relatorio/exportar/', views.exportar_relatorio_mensal, name='exportar_relatorio'),
]
