from django.urls import path
from . import views

urlpatterns = [
    path(
        'capturar-foto/<int:funcionario_id>/',
        views.capturar_foto_funcionario,
        name='capturar_foto_funcionario'
    ),
    path(
        'salvar-foto/',
        views.salvar_foto_funcionario,
        name='salvar_foto_funcionario'
    ),
]
