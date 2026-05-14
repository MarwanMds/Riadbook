from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        TRAVELER = "traveler", _("Voyageur")
        OWNER    = "owner",    _("Hôtelier")
        ADMIN    = "admin",    _("Administrateur")

    class Language(models.TextChoices):
        FR = "fr", "Français"
        AR = "ar", "العربية"
        EN = "en", "English"

    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    phone      = models.CharField(max_length=20, blank=True)
    avatar     = models.ImageField(upload_to="avatars/", null=True, blank=True)

    role               = models.CharField(max_length=10, choices=Role.choices, default=Role.TRAVELER)
    preferred_language = models.CharField(max_length=2,  choices=Language.choices, default=Language.FR)

    is_active                = models.BooleanField(default=True)
    is_staff                 = models.BooleanField(default=False)
    is_email_verified        = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login  = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table            = "users"
        verbose_name        = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

    @property
    def full_name(self): return f"{self.first_name} {self.last_name}"

    @property
    def is_traveler(self): return self.role == self.Role.TRAVELER
    @property
    def is_owner(self):    return self.role == self.Role.OWNER
    @property
    def is_admin(self):    return self.role == self.Role.ADMIN
