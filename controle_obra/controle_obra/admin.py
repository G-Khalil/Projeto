from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from acessos.models import AcessoObra
from funcionarios.models import Funcionario
from empresas.models import Empresa


class MeuAdminSite(admin.AdminSite):
    site_header = 'Administração da Obra'
    site_title = 'Admin Obra'
    index_title = 'Painel de Controle'

    def each_context(self, request):
        """
        Adiciona a URL da presença de hoje no contexto do admin,
        para usar no template base_site.html.
        """
        context = super().each_context(request)
        # nome da URL da tela de presença de hoje
        context['link_presenca_hoje'] = reverse('lista_presenca_hoje')
        return context


# instância do admin personalizado
admin_site = MeuAdminSite(name='meu_admin')

# registrar os modelos no admin personalizado
admin_site.register(AcessoObra)
admin_site.register(Funcionario)
admin_site.register(Empresa)
