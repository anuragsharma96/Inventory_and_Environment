from django.apps import AppConfig


class InventoryappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventoryapp'
    def ready(self):
        import inventoryapp.signals
