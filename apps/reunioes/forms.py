from django import forms
from .models import Reuniao


class ReuniaoForm(forms.ModelForm):
    class Meta:
        model = Reuniao
        fields = ["cliente", "tipo", "data", "duracao_minutos", "consultor", "participantes", "link_gravacao", "resumo", "proximos_passos"]
        widgets = {
            "data": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "resumo": forms.Textarea(attrs={"rows": 4}),
            "proximos_passos": forms.Textarea(attrs={"rows": 3}),
            "participantes": forms.Textarea(attrs={"rows": 2}),
        }
