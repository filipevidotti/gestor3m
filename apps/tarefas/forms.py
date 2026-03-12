from django import forms

from apps.accounts.models import User

from .models import (
    ComentarioTarefa,
    EtapaTarefa,
    EtiquetaTarefa,
    SubTarefa,
    Tarefa,
    TipoTarefa,
)


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = [
            "titulo",
            "descricao",
            "cliente",
            "responsavel",
            "tipo",
            "etapa",
            "prioridade",
            "prazo",
            "etiquetas",
        ]
        widgets = {
            "prazo": forms.DateInput(attrs={"type": "date"}),
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "etiquetas": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsavel"].queryset = User.objects.filter(
            role__in=["gestor", "consultor", "seller", "funcionario", "comercial"],
            is_active=True,
        ).order_by("first_name")
        self.fields["etapa"].queryset = EtapaTarefa.objects.all()
        self.fields["cliente"].required = False
        self.fields["descricao"].required = False


class SubTarefaForm(forms.ModelForm):
    class Meta:
        model = SubTarefa
        fields = ["titulo", "responsavel"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsavel"].required = False
        self.fields["responsavel"].queryset = User.objects.filter(
            is_active=True
        ).order_by("first_name")


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = ComentarioTarefa
        fields = ["texto"]
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 2, "placeholder": "Adicionar comentário..."}),
        }


class EtapaTarefaForm(forms.ModelForm):
    class Meta:
        model = EtapaTarefa
        fields = ["nome", "cor", "icone", "ordem", "is_concluido"]
        widgets = {
            "cor": forms.TextInput(attrs={"type": "color"}),
        }


class EtiquetaTarefaForm(forms.ModelForm):
    class Meta:
        model = EtiquetaTarefa
        fields = ["nome", "cor"]
        widgets = {
            "cor": forms.TextInput(attrs={"type": "color"}),
        }


class TipoTarefaForm(forms.ModelForm):
    class Meta:
        model = TipoTarefa
        fields = ["nome", "icone", "cor"]
        widgets = {
            "cor": forms.TextInput(attrs={"type": "color"}),
        }
