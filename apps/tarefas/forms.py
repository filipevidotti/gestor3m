from django import forms
from apps.accounts.models import User
from .models import Tarefa, TipoTarefa


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ["cliente", "responsavel", "tipo", "descricao", "prioridade", "prazo", "status"]
        widgets = {
            "prazo": forms.DateInput(attrs={"type": "date"}),
            "descricao": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Incluir funcionarios no campo responsavel
        self.fields["responsavel"].queryset = User.objects.filter(
            role__in=["gestor", "consultor", "seller", "funcionario"],
            is_active=True,
        ).order_by("first_name")


class TipoTarefaForm(forms.ModelForm):
    class Meta:
        model = TipoTarefa
        fields = ["nome", "icone", "cor"]
        widgets = {
            "cor": forms.TextInput(attrs={"type": "color"}),
        }
