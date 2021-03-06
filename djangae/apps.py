from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class DjangaeConfig(AppConfig):
    name = 'djangae'
    verbose_name = _("Djangae")

    def ready(self):
        from .patches.contenttypes import patch
        patch()
