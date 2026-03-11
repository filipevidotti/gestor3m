from django import forms
from .models import Treinamento, TreinamentoRealizado


class TreinamentoForm(forms.ModelForm):
    class Meta:
        model = Treinamento
        fields = ["titulo", "categoria", "descricao", "conteudo_url", "material", "duracao_minutos"]
        widgets = {"descricao": forms.Textarea(attrs={"rows": 3})}


class TreinamentoRealizadoForm(forms.ModelForm):
    class Meta:
        model = TreinamentoRealizado
        fields = ["treinamento", "cliente", "data", "observacoes"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 2}),
        }


class RegistrarTreinamentoForm(forms.ModelForm):
    """Form para consultor registrar treinamento realizado dentro do detalhe do cliente."""

    class Meta:
        model = TreinamentoRealizado
        fields = ["treinamento", "data", "observacoes", "material_especifico"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cliente = cliente
        if cliente:
            # Excluir treinamentos já realizados por este cliente
            ja_realizados = TreinamentoRealizado.objects.filter(
                cliente=cliente
            ).values_list("treinamento_id", flat=True)
            self.fields["treinamento"].queryset = Treinamento.objects.exclude(
                pk__in=ja_realizados
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cliente:
            instance.cliente = self.cliente
        if commit:
            instance.save()
        return instance
