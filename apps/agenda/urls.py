from django.urls import path

from . import views

app_name = "agenda"

urlpatterns = [
    # Consultor (autenticadas)
    path("config/", views.agenda_config, name="config"),
    path("visualizar/", views.agenda_visualizar, name="visualizar"),
    path("eventos-json/", views.agenda_eventos_json, name="eventos_json"),
    path("agendamentos/", views.agenda_agendamentos, name="agendamentos"),
    path("agendamentos/<int:pk>/cancelar/", views.agenda_cancelar, name="cancelar"),
    path("agendamentos/<int:pk>/status/", views.agenda_marcar_status, name="marcar_status"),

    # Google OAuth
    path("google/conectar/", views.google_auth_inicio, name="google_auth_inicio"),
    path("google/callback/", views.google_auth_callback, name="google_auth_callback"),
    path("google/desconectar/", views.google_desconectar, name="google_desconectar"),

    # Público (sem login)
    path("c/<slug:slug>/", views.publico_agenda, name="publico_agenda"),
    path("c/<slug:slug>/horarios/", views.publico_horarios, name="publico_horarios"),
    path("c/<slug:slug>/agendar/", views.publico_agendar, name="publico_agendar"),
    path("cancelar/<uuid:token>/", views.publico_cancelar, name="publico_cancelar"),
]
