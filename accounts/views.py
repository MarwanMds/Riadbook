import secrets
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import RegisterForm, LoginForm, ProfileForm
from .models import User


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
def register_view(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_url(request.user))

    form = RegisterForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email_verification_token = secrets.token_hex(32)
        user.save()
        # Send verification email (imported lazily to avoid circular imports)
        from .emails import send_verification_email
        send_verification_email(request, user)
        messages.success(request,
            "Compte créé ! Vérifiez votre e-mail pour activer votre compte.")
        return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------
def verify_email_view(request, token):
    try:
        user = User.objects.get(email_verification_token=token, is_email_verified=False)
    except User.DoesNotExist:
        messages.error(request, "Lien de vérification invalide ou déjà utilisé.")
        return redirect("accounts:login")

    user.is_email_verified     = True
    user.email_verification_token = ""
    user.save(update_fields=["is_email_verified", "email_verification_token"])
    login(request, user,
          backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, "E-mail vérifié ! Bienvenue sur RiadBook.")
    return redirect(_dashboard_url(user))


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect(_dashboard_url(request.user))

    form = LoginForm(request, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user,
              backend="django.contrib.auth.backends.ModelBackend")
        next_url = request.GET.get("next") or _dashboard_url(user)
        return redirect(next_url)

    return render(request, "accounts/login.html", {"form": form})


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
def logout_view(request):
    logout(request)
    return redirect("public:home")


# ---------------------------------------------------------------------------
# Profile (traveler / owner)
# ---------------------------------------------------------------------------
@login_required
def profile_view(request):
    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour avec succès.")
        return redirect("accounts:profile")

    return render(request, "accounts/profile.html", {"form": form})


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _dashboard_url(user):
    if user.role == User.Role.ADMIN:
        return "/admin-dashboard/"
    if user.role == User.Role.OWNER:
        return "/owner/"
    return "/dashboard/"