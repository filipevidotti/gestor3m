from django.urls import path
from . import views

app_name = "anuncios"

urlpatterns = [
    # Curva ABC
    path("cliente/<int:cliente_pk>/curva-abc/", views.curva_abc, name="curva_abc"),
    path("cliente/<int:cliente_pk>/curva-abc/upload/", views.curva_abc_upload, name="curva_abc_upload"),

    # Métricas
    path("cliente/<int:cliente_pk>/metricas/", views.metricas, name="metricas"),
    path("cliente/<int:cliente_pk>/metricas/upload/", views.metricas_upload, name="metricas_upload"),

    # Atualizações
    path("cliente/<int:cliente_pk>/atualizacoes/", views.atualizacoes, name="atualizacoes"),
    path("cliente/<int:cliente_pk>/atualizacoes/upload/", views.atualizacoes_upload, name="atualizacoes_upload"),
]
