from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("", views.listar_leads, name="listar"),
    path("kanban/", views.kanban, name="kanban"),
    path("kanban/mover/", views.kanban_mover, name="kanban_mover"),
    path("leads/novo/", views.criar_lead, name="criar_lead"),
    path("leads/<int:pk>/", views.detalhe_lead, name="detalhe_lead"),
    path("leads/<int:pk>/editar/", views.editar_lead, name="editar_lead"),
    path("leads/<int:pk>/excluir/", views.excluir_lead, name="excluir_lead"),
    path("leads/<int:pk>/converter/", views.converter_lead, name="converter_lead"),
    path("leads/<int:pk>/atividade/", views.adicionar_atividade, name="adicionar_atividade"),
    path("leads/<int:pk>/lembrete/", views.criar_lembrete, name="criar_lembrete"),
    path("leads/<int:pk>/agendar/", views.agendar_reuniao, name="agendar_reuniao"),
    path("leads/<int:pk>/proposta/", views.criar_proposta, name="criar_proposta"),
    path("oportunidades/nova/<int:lead_pk>/", views.criar_oportunidade, name="criar_oportunidade"),
    path("oportunidades/<int:pk>/editar/", views.editar_oportunidade, name="editar_oportunidade"),
    path("config/", views.config_etapas, name="config_etapas"),
    path("config/<int:pk>/editar/", views.config_etapa_editar, name="config_etapa_editar"),
    path("config/<int:pk>/excluir/", views.config_etapa_excluir, name="config_etapa_excluir"),
]
