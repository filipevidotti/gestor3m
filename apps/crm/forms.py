from django import forms

from apps.accounts.models import User
from .models import Lead, Oportunidade, EtapaCRM, AtividadeCRM, LembreteCRM


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["nome", "empresa", "telefone", "email", "nicho", "origem", "observacoes"]


class OportunidadeForm(forms.ModelForm):
    class Meta:
        model = Oportunidade
        fields = ["titulo", "valor_estimado", "etapa", "previsao_fechamento"]


class EtapaCRMForm(forms.ModelForm):
    class Meta:
        model = EtapaCRM
        fields = ["nome", "descricao", "cor", "ordem", "is_ganho", "is_perdido"]


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = AtividadeCRM
        fields = ["tipo", "descricao"]


class LembreteForm(forms.ModelForm):
    class Meta:
        model = LembreteCRM
        fields = ["data_hora", "descricao", "enviar_whatsapp", "enviar_email"]
        widgets = {
            "data_hora": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class ConversaoForm(forms.Form):
    consultor = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=["gestor", "consultor"]),
        label="Consultor responsável",
    )
    tipo_consultoria = forms.ChoiceField(
        choices=[("estrategica", "Estratégica"), ("operacional", "Operacional")],
        label="Tipo de consultoria",
    )
    data_inicio = forms.DateField(
        label="Data de início",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
