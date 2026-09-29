from django.apps import AppConfig


class CommissionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.commissions"
    verbose_name = "Шимтгэл"

    def ready(self):
        import apps.commissions.signals  # noqa: F401
