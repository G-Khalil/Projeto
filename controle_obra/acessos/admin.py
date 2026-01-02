from django.contrib import admin
from .models import AcessoObra

@admin.register(AcessoObra)
class AcessoObraAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data', 'hora_entrada', 'hora_saida')
    list_filter = ('data', 'funcionario__empresa')
