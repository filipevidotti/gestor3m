from django import forms
from django.contrib.auth import get_user_model

from .models import Consultor

User = get_user_model()


class ConsultorForm(forms.ModelForm):
    class Meta:
        model = Consultor
        fields = ["usuario", "especialidade", "bio", "max_clientes"]


class VendedorForm(forms.ModelForm):
    """Form para criar/editar usuário com role=comercial."""

    password = forms.CharField(
        label="Senha", widget=forms.PasswordInput, required=False,
        help_text="Deixe em branco para manter a senha atual (edição).",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "username", "telefone", "password"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["password"].required = False
        else:
            self.fields["password"].required = True
            self.fields["password"].help_text = ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.COMERCIAL
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
