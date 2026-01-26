from django.contrib import admin
from .models import Funcionario

class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'funcao', 'telefone', 'tem_foto', 'tem_facial_data')
    fields = ('nome', 'empresa', 'funcao', 'telefone', 'foto', 'facial_data', 'facial_registered_at')
    readonly_fields = ('facial_data', 'facial_registered_at')

    # BUSCA POR NOME
    search_fields = ('nome', 'empresa__nome', 'funcao')

    # FILTRO POR EMPRESA
    list_filter = ('empresa', 'funcao')

    # ORDENAÇÃO
    ordering = ('empresa', 'nome')

    def tem_foto(self, obj):
        return bool(obj.foto)
    tem_foto.boolean = True
    tem_foto.short_description = 'Tem Foto?'

    def tem_facial_data(self, obj):
        if obj.facial_data:
            import json
            try:
                data = json.loads(obj.facial_data)
                if data.get('encoding'):
                    return True
            except:
                pass
        return False
    tem_facial_data.boolean = True
    tem_facial_data.short_description = 'Dados Faciais?'

admin.site.register(Funcionario, FuncionarioAdmin)
