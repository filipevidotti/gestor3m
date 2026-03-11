from django import forms
from .models import DataPromocional, PreparacaoPromocional


class DataPromocionalForm(forms.ModelForm):
    class Meta:
        model = DataPromocional
        fields = [
            "nome", "tipo", "importancia", "data_inicio", "data_fim",
            "inscricao_inicio", "inscricao_fim", "descricao", "dicas",
            "cor", "icone", "link_ml", "antecedencia_preparo_dias",
        ]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
            "inscricao_inicio": forms.DateInput(attrs={"type": "date"}),
            "inscricao_fim": forms.DateInput(attrs={"type": "date"}),
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "dicas": forms.Textarea(attrs={"rows": 4}),
        }


class PreparacaoForm(forms.ModelForm):
    class Meta:
        model = PreparacaoPromocional
        fields = [
            "status", "desconto_medio", "budget_ads", "observacoes",
            "resultado_vendas", "resultado_faturamento",
        ]
        widgets = {
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }
