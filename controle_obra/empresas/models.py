from django.db import models

class Empresa(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18, blank=True, null=True)

    def __str__(self):
        return self.nome
