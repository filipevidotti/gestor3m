from django import forms
from apps.accounts.models import User
from .models import PlanoAcao, ItemPlano


class PlanoAcaoForm(forms.ModelForm):
    class Meta:
        model = PlanoAcao
        fields = ["cliente", "titulo", "tipo", "descricao"]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class ItemPlanoForm(forms.ModelForm):
    class Meta:
        model = ItemPlano
        fields = ["descricao", "responsavel", "prioridade", "prazo", "status"]
        widgets = {
            "prazo": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Incluir funcionarios no campo responsavel
        self.fields["responsavel"].queryset = User.objects.filter(
            role__in=["gestor", "consultor", "seller", "funcionario"],
            is_active=True,
        ).order_by("first_name")
