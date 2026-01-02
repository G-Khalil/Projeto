from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Funcionario


class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'empresa', 'funcao', 'telefone', 'tem_foto')
    fields = ('nome', 'empresa', 'funcao', 'telefone', 'foto', 'botao_capturar_foto')
    readonly_fields = ('botao_capturar_foto',)

    def tem_foto(self, obj):
        return bool(obj.foto)
    tem_foto.boolean = True
    tem_foto.short_description = 'Tem Foto?'

    def botao_capturar_foto(self, obj):
        if obj.id:
            url = reverse('capturar_foto_funcionario', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" '
                'style="background:#1976d2;color:white;padding:8px 12px;'
                'border-radius:4px;text-decoration:none;">📷 Capturar Foto com Webcam</a>',
                url
            )
        return format_html('<p>Salve o funcionário primeiro para capturar a foto.</p>')
    botao_capturar_foto.short_description = 'Captura de Foto'


admin.site.register(Funcionario, FuncionarioAdmin)
