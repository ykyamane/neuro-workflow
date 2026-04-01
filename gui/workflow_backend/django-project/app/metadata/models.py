"""
Metadata app models.
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CustomDatabase(models.Model):
    """User-defined custom database source for parameter suggestions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    base_url = models.URLField()
    api_key = models.CharField(max_length=500, blank=True, null=True)
    config = models.JSONField(default=dict, blank=True, help_text="Additional configuration (headers, query params, auth type, etc.)")
    adapter_type = models.CharField(max_length=50, default="rest_api")
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_tested = models.DateTimeField(null=True, blank=True)
    test_result = models.TextField(blank=True, null=True)
    test_error = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="custom_databases",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Custom database"
        verbose_name_plural = "Custom databases"

    def __str__(self):
        return self.name

    def get_config_dict(self):
        """Return config as dict for adapter initialization."""
        return self.config if isinstance(self.config, dict) else {}

    def to_adapter_config(self, openai_client=None):
        """Build config dict for GenericDatabaseAdapter."""
        cfg = {
            "base_url": self.base_url.rstrip("/"),
            "api_key": self.api_key or "",
            "source_name": self.name,
            "enabled": self.is_active,
            "openai_client": openai_client,
            **self.get_config_dict(),
        }
        cfg.setdefault("adapter_type", self.adapter_type)
        return cfg
