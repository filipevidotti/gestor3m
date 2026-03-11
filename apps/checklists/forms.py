from django import forms
from .models import (
    ChecklistTemplate, ChecklistTemplateItem, ChecklistCategory,
    ChecklistExecution, ChecklistExecutionItem, Evidence,
)


class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = ["nome", "descricao", "icone", "target_audience", "tipo"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
        }


class ChecklistTemplateItemForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplateItem
        fields = ["category", "descricao", "instrucoes", "ordem", "requires_evidence", "requires_note"]
        widgets = {
            "instrucoes": forms.Textarea(attrs={"rows": 2}),
        }


ChecklistTemplateItemFormSet = forms.inlineformset_factory(
    ChecklistTemplate,
    ChecklistTemplateItem,
    form=ChecklistTemplateItemForm,
    extra=3,
    can_delete=True,
)


class ChecklistExecutionForm(forms.ModelForm):
    class Meta:
        model = ChecklistExecution
        fields = ["template", "cliente"]


class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ["file", "description"]
