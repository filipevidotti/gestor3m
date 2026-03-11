from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("contas/", include("apps.accounts.urls")),
    path("clientes/", include("apps.clientes.urls")),
    path("consultores/", include("apps.consultores.urls")),
    path("diagnosticos/", include("apps.diagnosticos.urls")),
    path("planos/", include("apps.planos.urls")),
    path("tarefas/", include("apps.tarefas.urls")),
    path("checklists/", include("apps.checklists.urls")),
    path("reunioes/", include("apps.reunioes.urls")),
    path("treinamentos/", include("apps.treinamentos.urls")),
    path("financeiro/", include("apps.financeiro.urls")),
    path("notificacoes/", include("apps.notificacoes.urls")),
    path("portal/", include("apps.portal.urls")),
    path("gamificacao/", include("apps.gamificacao.urls")),
    path("anuncios/", include("apps.anuncios.urls")),
    path("swot/", include("apps.swot.urls")),
    path("propostas/", include("apps.propostas.urls")),
    path("agenda/", include("apps.agenda.urls")),
    path("timesheet/", include("apps.timesheet.urls")),
    path("nps/", include("apps.nps.urls")),
    path("relatorios/", include("apps.relatorios.urls")),
    path("conhecimento/", include("apps.conhecimento.urls")),
    path("crm/", include("apps.crm.urls")),
    path("ia/", include("apps.ia.urls")),
    path("jornadas/", include("apps.jornadas.urls")),
    path("calendario/", include("apps.calendario_promocional.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar
        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    except ImportError:
        pass
