from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class RegisterForm(forms.ModelForm):
    password  = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")
    role      = forms.ChoiceField(
        choices=[
            (User.Role.TRAVELER, "Je suis un voyageur"),
            (User.Role.OWNER,    "Je suis hôtelier / propriétaire de riad"),
        ],
        widget=forms.RadioSelect,
        initial=User.Role.TRAVELER,
    )

    class Meta:
        model  = User
        fields = ["first_name", "last_name", "email", "phone", "role"]

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cet e-mail.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        if p1:
            try:
                validate_password(p1)
            except forms.ValidationError as e:
                self.add_error("password", e)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email    = forms.EmailField(label="Adresse e-mail")
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self._user   = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned  = super().clean()
        email    = cleaned.get("email", "").lower()
        password = cleaned.get("password", "")
        if email and password:
            self._user = authenticate(self.request, username=email, password=password)
            if self._user is None:
                raise forms.ValidationError("E-mail ou mot de passe incorrect.")
            if not self._user.is_active:
                raise forms.ValidationError("Ce compte est désactivé.")
        return cleaned

    def get_user(self):
        return self._user


class ProfileForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ["first_name", "last_name", "phone", "avatar", "preferred_language"]
