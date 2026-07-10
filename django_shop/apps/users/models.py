from __future__ import annotations
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserManager(BaseUserManager['User']):
    def create_user(self, email: str, password: str | None = None, **extra_fields) -> 'User':
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> 'User':
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email: models.EmailField[str, str] = models.EmailField(unique=True, verbose_name="Email")
    phone: models.CharField[str, str] = models.CharField(max_length=15, blank=True, null=True, verbose_name='Telephone number')
    address: models.CharField = models.CharField(max_length=255, blank=True, null=True, verbose_name='Address')
    city: models.CharField = models.CharField(max_length=30, blank=True, null=True, verbose_name='City')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()  # type: ignore[assignment]

    def __str__(self) -> str:
        return self.email