from django.contrib import admin
from .models import AcessoObra

@admin.register(AcessoObra)
class AcessoObraAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'empresa', 'data', 'hora_entrada', 'hora_saida')
    list_filter = ('empresa', 'data', 'funcionario')
    search_fields = ('funcionario__nome', 'empresa__nome')
    ordering = ('empresa', 'data', 'funcionario')
