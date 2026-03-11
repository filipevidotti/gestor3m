from django.db import migrations


MODULOS = [
    {"slug": "dashboard", "nome": "Dashboard", "icone": "home", "ordem": 1},
    {"slug": "clientes", "nome": "Clientes", "icone": "users", "ordem": 2},
    {"slug": "pipeline", "nome": "Pipeline", "icone": "kanban", "ordem": 3},
    {"slug": "consultores", "nome": "Consultores", "icone": "user-check", "ordem": 4},
    {"slug": "diagnosticos", "nome": "Diagnósticos", "icone": "bar-chart", "ordem": 5},
    {"slug": "checklists", "nome": "Checklists", "icone": "clipboard-check", "ordem": 6},
    {"slug": "tarefas", "nome": "Tarefas", "icone": "check-circle", "ordem": 7},
    {"slug": "reunioes", "nome": "Reuniões", "icone": "video", "ordem": 8},
    {"slug": "treinamentos", "nome": "Treinamentos", "icone": "book", "ordem": 9},
    {"slug": "financeiro", "nome": "Financeiro", "icone": "dollar-sign", "ordem": 10},
    {"slug": "propostas", "nome": "Propostas", "icone": "file-text", "ordem": 11},
    {"slug": "gamificacao", "nome": "Ranking", "icone": "star", "ordem": 12},
    {"slug": "anuncios", "nome": "Anúncios", "icone": "megaphone", "ordem": 13},
    {"slug": "swot", "nome": "SWOT", "icone": "grid", "ordem": 14},
]


def populate(apps, schema_editor):
    Modulo = apps.get_model("accounts", "Modulo")
    for m in MODULOS:
        Modulo.objects.get_or_create(slug=m["slug"], defaults=m)


def reverse(apps, schema_editor):
    Modulo = apps.get_model("accounts", "Modulo")
    Modulo.objects.filter(slug__in=[m["slug"] for m in MODULOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_modulo_user_modulos"),
    ]

    operations = [
        migrations.RunPython(populate, reverse),
    ]
