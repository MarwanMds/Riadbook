from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _site_url():
    return getattr(settings, "SITE_URL", "https://www.riadbook.ma")


def send_property_approved(property_obj):
    """
    Email 2a — Property approved.
    Sent to the owner when the admin approves their listing.
    """
    owner = property_obj.owner
    subject = f"✓ Votre établissement « {property_obj.name} » est approuvé — RiadBook Maroc"
    context = {
        "owner":    owner,
        "property": property_obj,
        "site_url": _site_url(),
    }
    html_message = render_to_string("properties/emails/property_approved.html", context)
    plain_message = (
        f"Bonjour {owner.first_name},\n\n"
        f"Bonne nouvelle ! Votre établissement « {property_obj.name} » ({property_obj.city.name}) "
        f"a été approuvé par notre équipe et est maintenant visible sur RiadBook Maroc.\n\n"
        f"Accédez à votre espace hôtelier : {_site_url()}/owner/dashboard/\n\n"
        f"L'équipe RiadBook Maroc"
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[owner.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_property_rejected(property_obj, reason=""):
    """
    Email 2b — Property rejected.
    Sent to the owner when the admin rejects their listing.
    """
    owner = property_obj.owner
    subject = f"Votre établissement « {property_obj.name} » — Demande non approuvée"
    context = {
        "owner":            owner,
        "property":         property_obj,
        "rejection_reason": reason,
        "site_url":         _site_url(),
    }
    html_message = render_to_string("properties/emails/property_rejected.html", context)
    plain_message = (
        f"Bonjour {owner.first_name},\n\n"
        f"Après examen, votre établissement « {property_obj.name} » n'a pas pu être approuvé "
        f"pour le moment.\n\n"
        + (f"Motif : {reason}\n\n" if reason else "")
        + f"Vous pouvez modifier votre dossier et le soumettre à nouveau : "
        f"{_site_url()}/owner/property/edit/\n\n"
        f"L'équipe RiadBook Maroc"
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[owner.email],
        html_message=html_message,
        fail_silently=False,
    )
