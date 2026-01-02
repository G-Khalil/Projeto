from django.db import models
from funcionarios.models import Funcionario


class AcessoObra(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    data = models.DateField(auto_now_add=True)
    hora_entrada = models.TimeField(null=True, blank=True)
    hora_saida = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.funcionario.nome} - {self.data}'
