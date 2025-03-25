from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chat"

def ready(self):
    import os

    from django.conf import settings
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'files'), exist_ok=True)
