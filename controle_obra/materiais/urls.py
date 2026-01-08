from django.urls import path
from . import views
from . import reconhecer_material_api

app_name = 'materiais'

urlpatterns = [
    # APIs de reconhecimento facial
    path('api/reconhecer-emprestimo/', reconhecer_material_api.reconhecer_emprestimo_material, name='api_reconhecer_emprestimo'),
    path('api/reconhecer-consumo/', reconhecer_material_api.reconhecer_saida_consumo, name='api_reconhecer_consumo'),
]
