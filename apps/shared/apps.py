from django.apps import AppConfig


class SharedConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shared"
    verbose_name = "Систем - Нийтлэг сан"

    def ready(self):
        from apps.shared.localization import apply_mongolian_translations

        apply_mongolian_translations()
