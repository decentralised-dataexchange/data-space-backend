import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from django.db import models

from organisation.models import Organisation


class OAuth2Clients(models.Model):
    """OAuth 2.0 Clients for organisations to create multiple clients"""

    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    client_id: models.CharField[str, str] = models.CharField(
        max_length=255, unique=True, db_index=True
    )
    client_secret: models.CharField[str, str] = models.CharField(max_length=255)
    name: models.CharField[str, str] = models.CharField(
        max_length=255, help_text="Human-readable name for the client"
    )
    description: models.TextField[str, str] = models.TextField(
        blank=True, help_text="Optional description of the client"
    )
    organisation: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="oauth_clients"
    )
    is_active: models.BooleanField[bool, bool] = models.BooleanField(default=True)
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "oauth2_clients"
        verbose_name = "OAuth2 Client"
        verbose_name_plural = "OAuth2 Clients"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "name"], name="uniq_organisation_client_name"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.client_id}) - {self.organisation.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        # Generate client_id and client_secret if not provided
        if not self.client_id:
            self.client_id = f"client_{uuid.uuid4().hex[:12]}"
        if not self.client_secret:
            self.client_secret = f"secret_{uuid.uuid4().hex[:24]}"
        super().save(*args, **kwargs)


class OrganisationOAuth2Clients(models.Model):
    """Organisation OAuth 2.0 Clients for organisations to configure multiple clients"""

    id: models.UUIDField[UUID, UUID] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    client_id: models.CharField[str, str] = models.CharField(
        max_length=255, unique=True, db_index=True
    )
    client_secret: models.CharField[str, str] = models.CharField(max_length=255)
    name: models.CharField[str, str] = models.CharField(
        max_length=255, help_text="Human-readable name for the client"
    )
    description: models.TextField[str, str] = models.TextField(
        blank=True, help_text="Optional description of the client"
    )
    organisation: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="organisation_oauth_clients",
    )
    is_active: models.BooleanField[bool, bool] = models.BooleanField(default=True)
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )
    updated_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "organisation_oauth2_clients"
        verbose_name = "Organisation OAuth2 Client"
        verbose_name_plural = "Organisation OAuth2 Clients"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "name"], name="uniq_client_name"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.client_id}) - {self.organisation.name}"
