from django.urls import path

from . import views

app_name = "ia"

urlpatterns = [
    path("insights/", views.listar_insights, name="listar_insights"),
    path("insights/<int:pk>/lido/", views.marcar_lido, name="marcar_lido"),
]
