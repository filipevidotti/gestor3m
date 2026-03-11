from django.urls import path

from . import views

app_name = "swot"

urlpatterns = [
    path("cliente/<int:cliente_pk>/", views.listar, name="listar"),
    path("cliente/<int:cliente_pk>/criar/", views.criar, name="criar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
    path("<int:pk>/exportar-excel/", views.exportar_excel, name="exportar_excel"),
    path("<int:pk>/exportar-pdf/", views.exportar_pdf, name="exportar_pdf"),
]
