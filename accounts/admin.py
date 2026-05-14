from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ("email", "full_name", "role", "is_active", "is_email_verified", "date_joined")
    list_filter   = ("role", "is_active", "is_email_verified")
    search_fields = ("email", "first_name", "last_name")
    ordering      = ("-date_joined",)

    fieldsets = (
        (None,           {"fields": ("email", "password")}),
        ("Informations", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        ("Rôle",         {"fields": ("role", "preferred_language")}),
        ("Statut",       {"fields": ("is_active", "is_staff", "is_superuser",
                                     "is_email_verified", "email_verification_token")}),
        ("Dates",        {"fields": ("date_joined", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "first_name", "last_name", "role", "password1", "password2"),
        }),
    )
    readonly_fields = ("date_joined", "last_login")
