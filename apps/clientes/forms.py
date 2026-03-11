from django import forms
from .models import Cliente, EtapaPipeline


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "empresa", "cnpj", "nicho", "consultor",
            "tipo_consultoria", "data_inicio", "status", "etapa",
            "telefone", "email", "logo",
            "ml_nickname", "ml_seller_id", "ml_reputacao",
            "observacoes",
        ]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class EtapaPipelineForm(forms.ModelForm):
    class Meta:
        model = EtapaPipeline
        fields = ["nome", "descricao", "cor", "ordem"]
        widgets = {
            "cor": forms.TextInput(attrs={"type": "color"}),
        }
