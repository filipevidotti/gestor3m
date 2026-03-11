from django import forms
from .models import DiagnosticTemplate, DiagnosticQuestion, Diagnostic


class DiagnosticTemplateForm(forms.ModelForm):
    class Meta:
        model = DiagnosticTemplate
        fields = ["nome", "descricao"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
        }


class DiagnosticQuestionForm(forms.ModelForm):
    class Meta:
        model = DiagnosticQuestion
        fields = ["categoria", "texto", "tipo", "weight", "is_inverted", "options", "ordem"]
        widgets = {
            "options": forms.Textarea(attrs={"rows": 2}),
        }


DiagnosticQuestionFormSet = forms.inlineformset_factory(
    DiagnosticTemplate,
    DiagnosticQuestion,
    form=DiagnosticQuestionForm,
    extra=3,
    can_delete=True,
)


class DiagnosticForm(forms.ModelForm):
    class Meta:
        model = Diagnostic
        fields = ["template", "cliente", "mes", "ano"]
