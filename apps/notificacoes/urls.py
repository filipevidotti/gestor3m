from django.urls import path
from . import views

app_name = "notificacoes"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("<int:pk>/lida/", views.marcar_lida, name="marcar_lida"),
]
