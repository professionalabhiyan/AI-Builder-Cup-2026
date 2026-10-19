import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, full_name="Enterprise Operator", role="SYSTEM_ADMIN", password=None):
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(
            email=self.normalize_email(email),
            full_name=full_name,
            role=role,
            is_active=True,
            is_staff=(role == "SUPER_ADMIN"),
            is_superuser=(role == "SUPER_ADMIN"),
            is_2fa_enabled=True,
        )
        user.set_password(password or "AeroGuard@2026!")
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name="Super Admin", password=None):
        return self.create_user(email=email, full_name=full_name, role="SUPER_ADMIN", password=password or "AeroGuard@2026!")


class User(AbstractBaseUser):
    ROLE_CHOICES = [
        ("SUPER_ADMIN", "Super Admin"),
        ("SYSTEM_ADMIN", "System Admin"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150, default="Enterprise Admin")
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="SUPER_ADMIN")
    department = models.CharField(max_length=100, default="Intelligent Operations")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)
    is_2fa_enabled = models.BooleanField(default=True)
    is_2fa_setup_complete = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True, default="")
    pending_totp_secret = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
