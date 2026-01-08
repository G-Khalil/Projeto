from django.db import models
from django.utils import timezone
from funcionarios.models import Funcionario
import json

# TIPO DE MATERIAL
class TipoMaterial(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    
    def __str__(self):
        return self.nome

# MATERIAL DE DEVOLUCAO (Ferramentas - Reconhecimento Facial)
class MaterialDevolucao(models.Model):
    STATUS_CHOICES = [
        ('disponivel', 'Disponivel'),
        ('emprestado', 'Emprestado'),
        ('danificado', 'Danificado'),
        ('perdido', 'Perdido'),
    ]
    
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    tipo = models.ForeignKey(TipoMaterial, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel')
    condicao = models.CharField(max_length=20, choices=[
        ('novo', 'Novo'),
        ('bom', 'Bom'),
        ('desgastado', 'Desgastado'),
        ('danificado', 'Danificado'),
    ])
    data_aquisicao = models.DateField()
    valor = models.DecimalField(max_digits=8, decimal_places=2)
    foto = models.ImageField(upload_to='materiais/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.nome} ({self.codigo}) - {self.status}"

# EMPRESTIMO DE MATERIAL COM RECONHECIMENTO FACIAL
class EmprestimoMaterial(models.Model):
    material = models.ForeignKey(MaterialDevolucao, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT)
    data_emprestimo = models.DateField(auto_now_add=True)
    hora_emprestimo = models.TimeField(auto_now_add=True)
    funcionario_responsavel_saida = models.CharField(max_length=100)
    
    # Reconhecimento Facial - Saida
    facial_data_saida = models.JSONField(null=True, blank=True)
    confianca_saida = models.FloatField(null=True, blank=True)
    
    data_devolucao = models.DateField(null=True, blank=True)
    hora_devolucao = models.TimeField(null=True, blank=True)
    funcionario_responsavel_entrada = models.CharField(max_length=100, null=True, blank=True)
    
    condicao_devolucao = models.CharField(max_length=20, choices=[
        ('igual', 'Igual ao emprestimo'),
        ('desgastado', 'Desgastado'),
        ('danificado', 'Danificado'),
        ('nao_devolvido', 'Nao devolvido'),
    ], null=True, blank=True)
    
    # Reconhecimento Facial - Entrada
    facial_data_entrada = models.JSONField(null=True, blank=True)
    confianca_entrada = models.FloatField(null=True, blank=True)
    
    observacoes = models.TextField(blank=True)
    
    def __str__(self):
        status = "Devolvido" if self.data_devolucao else "Emprestado"
        return f"{self.material.nome} - {self.funcionario.nome} ({status})"

# MATERIAL DE CONSUMO (Pregos, Arames, Madeira)
class MaterialConsumo(models.Model):
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    tipo = models.ForeignKey(TipoMaterial, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=50, unique=True)
    unidade = models.CharField(max_length=20, choices=[
        ('kg', 'Quilograma'),
        ('metro', 'Metro'),
        ('caixa', 'Caixa'),
        ('unidade', 'Unidade'),
        ('litro', 'Litro'),
    ])
    quantidade_estoque = models.IntegerField()
    quantidade_minima_alerta = models.IntegerField()
    valor_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    
    def __str__(self):
        return f"{self.nome} ({self.quantidade_estoque} {self.unidade})"

# SAIDA DE MATERIAL DE CONSUMO COM RECONHECIMENTO FACIAL
class SaidaMaterialConsumo(models.Model):
    material = models.ForeignKey(MaterialConsumo, on_delete=models.PROTECT)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.PROTECT)
    data_saida = models.DateField(auto_now_add=True)
    hora_saida = models.TimeField(auto_now_add=True)
    quantidade_saida = models.IntegerField()
    responsavel_saida = models.CharField(max_length=100)
    
    # Reconhecimento Facial
    facial_data = models.JSONField(null=True, blank=True)
    confianca = models.FloatField(null=True, blank=True)
    
    observacoes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.material.nome} - {self.quantidade_saida} {self.material.unidade} ({self.funcionario.nome})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.material.quantidade_estoque -= self.quantidade_saida
        self.material.save()
