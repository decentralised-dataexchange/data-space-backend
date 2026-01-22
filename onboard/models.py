from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from onboard.managers import DataspaceUserManager


class DataspaceUser(AbstractBaseUser, PermissionsMixin):
    email: models.EmailField[str, str] = models.EmailField(
        _("email address"), unique=True
    )
    is_staff: models.BooleanField[bool, bool] = models.BooleanField(default=False)
    is_active: models.BooleanField[bool, bool] = models.BooleanField(default=True)
    date_joined: models.DateTimeField[str, str] = models.DateTimeField(
        default=timezone.now
    )
    name: models.CharField[str | None, str | None] = models.CharField(
        max_length=250, null=True, blank=True
    )

    USERNAME_FIELD: str = "email"
    REQUIRED_FIELDS: "list[str]" = []  # type: ignore[misc]

    objects: "DataspaceUserManager" = DataspaceUserManager()  # type: ignore[misc]

    def __str__(self) -> str:
        return str(self.email)
