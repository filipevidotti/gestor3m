from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Modulo, User


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "icone", "ordem")
    list_editable = ("ordem",)
    search_fields = ("nome", "slug")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "get_full_name", "role", "is_active")
    list_filter = ("role", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("3M Control", {"fields": ("role", "telefone", "avatar")}),
        ("Permissões de Módulo", {"fields": ("modulos",)}),
    )
    filter_horizontal = ("modulos",)
