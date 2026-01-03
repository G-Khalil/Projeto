from django.db import models
from empresas.models import Empresa

class Funcionario(models.Model):
    nome = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcao = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    foto = models.ImageField(upload_to='funcionarios/', null=True, blank=True)
    facial_data = models.JSONField(null=True, blank=True, help_text='Dados de reconhecimento facial capturados da câmera')
    facial_registered_at = models.DateTimeField(null=True, blank=True, help_text='Data/hora do registro facial')


    def __str__(self):
        return self.nome


