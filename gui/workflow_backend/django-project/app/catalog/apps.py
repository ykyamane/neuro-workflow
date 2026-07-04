from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app.catalog"
    verbose_name = "Dataset Catalog (MDB proxy)"
