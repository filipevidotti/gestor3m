from django import forms
from .models import Contrato, ContratoTemplate, Pagamento


class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ["cliente", "plano", "valor", "dia_vencimento", "data_inicio", "data_fim", "observacoes"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class ContratoTemplateForm(forms.ModelForm):
    class Meta:
        model = ContratoTemplate
        fields = ["nome", "conteudo"]
        widgets = {
            "conteudo": forms.Textarea(attrs={"rows": 15}),
        }


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ["contrato", "mes_referencia", "valor", "status", "data_pagamento"]
        widgets = {
            "mes_referencia": forms.DateInput(attrs={"type": "date"}),
            "data_pagamento": forms.DateInput(attrs={"type": "date"}),
        }
