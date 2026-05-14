from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_verification_email(request, user):
    subject  = "RiadBook Maroc — Vérifiez votre adresse e-mail"
    verify_url = request.build_absolute_uri(
        f"/accounts/verify/{user.email_verification_token}/"
    )
    html_message = render_to_string("accounts/emails/verify_email.html", {
        "user":       user,
        "verify_url": verify_url,
    })
    send_mail(
        subject,
        strip_tags(html_message),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=True,
    )
