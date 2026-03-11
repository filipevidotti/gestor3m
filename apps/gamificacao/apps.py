from django.apps import AppConfig


class GamificacaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.gamificacao"
    verbose_name = "Gamificacao"

    def ready(self):
        import apps.gamificacao.signals  # noqa: F401
