from django.urls import path

from . import views

app_name = "nps"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("criar/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/enviar/", views.enviar, name="enviar"),
    # Público (seller responde)
    path("responder/<uuid:token>/", views.responder, name="responder"),
]
