from django.contrib import admin
from .models import AcessoObra

@admin.register(AcessoObra)
class AcessoObraAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'get_empresa', 'data', 'hora_entrada', 'hora_saida')
    list_filter = ('funcionario__empresa', 'data', 'funcionario')
    search_fields = ('funcionario__nome', 'funcionario__empresa__nome')
    ordering = ('funcionario__empresa', 'data', 'funcionario')

    def get_empresa(self, obj):
        return obj.funcionario.empresa.nome if obj.funcionario and obj.funcionario.empresa else "N/A"
    get_empresa.short_description = 'Empresa'
    get_empresa.admin_order_field = 'funcionario__empresa'
