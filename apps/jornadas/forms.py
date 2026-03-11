from django import forms

from .models import JornadaTemplate, EtapaTemplate


class JornadaTemplateForm(forms.ModelForm):
    class Meta:
        model = JornadaTemplate
        fields = ["nome", "descricao", "tipo_consultoria", "icone", "cor"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ex: Jornada Iniciante ML"}),
            "descricao": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "tipo_consultoria": forms.Select(attrs={"class": "form-select"}),
            "cor": forms.TextInput(attrs={"type": "color", "class": "form-input w-16 h-10"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.clientes.models import Cliente
        self.fields["tipo_consultoria"].choices = [("", "Qualquer tipo")] + list(
            Cliente.TipoConsultoria.choices
        )


class EtapaTemplateForm(forms.ModelForm):
    class Meta:
        model = EtapaTemplate
        fields = [
            "nome", "descricao", "tipo", "ordem", "dias_offset",
            "duracao_dias", "is_obrigatoria", "condicao",
            "checklist_template", "treinamento", "diagnostico_template",
        ]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-input"}),
            "descricao": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "ordem": forms.NumberInput(attrs={"class": "form-input w-20"}),
            "dias_offset": forms.NumberInput(attrs={"class": "form-input w-24"}),
            "duracao_dias": forms.NumberInput(attrs={"class": "form-input w-24"}),
            "condicao": forms.Textarea(attrs={"class": "form-textarea", "rows": 2, "placeholder": "Ex: só se score_reputacao < 6"}),
        }
