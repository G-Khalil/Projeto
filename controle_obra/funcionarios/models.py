from django.db import models
from empresas.models import Empresa

class Funcionario(models.Model):
    nome = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcao = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    foto = models.ImageField(upload_to='funcionarios/', null=True, blank=True)

    def __str__(self):
        return self.nome
