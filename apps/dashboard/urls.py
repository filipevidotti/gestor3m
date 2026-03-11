from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.index, name="dashboard"),
    path("cliente/<int:pk>/evolucao/", views.evolucao_cliente, name="evolucao_cliente"),
    path("meu-dia/", views.meu_dia, name="meu_dia"),
]
