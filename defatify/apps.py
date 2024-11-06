from django.apps import AppConfig


class DefatifyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'defatify'

    def ready(self):
        import defatify.signals  # Import the signals
