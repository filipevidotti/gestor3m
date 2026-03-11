from django.urls import path
from . import views

app_name = "financeiro"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("novo/", views.criar_contrato, name="criar"),
    path("<int:pk>/", views.detalhe_contrato, name="detalhe"),
    path("<int:pk>/pagamento/", views.adicionar_pagamento, name="adicionar_pagamento"),
    path("<int:pk>/pagamento/<int:pag_pk>/pago/", views.marcar_pago, name="marcar_pago"),
    # Contrato PDF + Assinatura
    path("<int:pk>/gerar-pdf/", views.gerar_contrato_pdf, name="gerar_pdf"),
    path("<int:pk>/preview/", views.preview_contrato, name="preview_contrato"),
    path("<int:pk>/enviar-assinatura/", views.enviar_para_assinatura, name="enviar_assinatura"),
    path("<int:pk>/verificar-assinatura/", views.verificar_assinatura, name="verificar_assinatura"),
    # Templates de contrato
    path("templates/", views.config_templates, name="config_templates"),
    path("templates/<int:pk>/editar/", views.editar_template, name="editar_template"),
    path("templates/<int:pk>/excluir/", views.excluir_template, name="excluir_template"),
    # Asaas
    path("<int:pk>/integrar-asaas/", views.integrar_asaas, name="integrar_asaas"),
    path("<int:pk>/sincronizar/", views.sincronizar_pagamentos, name="sincronizar"),
    path("<int:pk>/pagamento/<int:pag_pk>/pix/", views.ver_pix, name="ver_pix"),
    path("<int:pk>/pagamento/<int:pag_pk>/boleto/", views.ver_boleto, name="ver_boleto"),
    path("webhook/asaas/", views.asaas_webhook, name="asaas_webhook"),
]
