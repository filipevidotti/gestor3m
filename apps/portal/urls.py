from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("checklists/", views.checklists, name="checklists"),
    path("checklists/<int:pk>/", views.checklist_detalhe, name="checklist_detalhe"),
    path("checklists/<int:pk>/executar/", views.checklist_executar, name="checklist_executar"),
    path("checklists/<int:pk>/salvar/", views.checklist_salvar, name="checklist_salvar"),
    path("checklists/<int:pk>/completar/", views.checklist_completar, name="checklist_completar"),
    path("diagnosticos/", views.diagnosticos, name="diagnosticos"),
    path("diagnosticos/<int:pk>/", views.diagnostico_detalhe, name="diagnostico_detalhe"),
    path("tarefas/", views.tarefas, name="tarefas"),
    path("tarefas/<int:pk>/concluir/", views.tarefa_concluir, name="tarefa_concluir"),
    path("reunioes/", views.reunioes, name="reunioes"),
    path("planos/", views.planos, name="planos"),
    path("planos/<int:pk>/", views.plano_detalhe, name="plano_detalhe"),
    path("treinamentos/", views.treinamentos, name="treinamentos"),
    path("evolucao/", views.minha_evolucao, name="minha_evolucao"),
    path("curva-abc/", views.anuncios_curva_abc, name="anuncios_curva_abc"),
    path("metricas/", views.anuncios_metricas, name="anuncios_metricas"),
    path("atualizacoes/", views.anuncios_atualizacoes, name="anuncios_atualizacoes"),
    path("atualizacoes/<int:pk>/feito/", views.anuncio_marcar_feito, name="anuncio_marcar_feito"),
    # Equipe
    path("equipe/", views.equipe_listar, name="equipe_listar"),
    path("equipe/criar/", views.equipe_criar, name="equipe_criar"),
    path("equipe/<int:pk>/editar/", views.equipe_editar, name="equipe_editar"),
    path("equipe/<int:pk>/desativar/", views.equipe_desativar, name="equipe_desativar"),
]
