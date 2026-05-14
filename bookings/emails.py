from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def _site_url():
    """Return base site URL from settings, default to production domain."""
    return getattr(settings, "SITE_URL", "https://www.riadbook.ma")


def send_booking_confirmation(booking):
    """
    Email 1 — Booking confirmation.
    Sent to the traveler right after a booking is confirmed.
    """
    subject = (
        f"✓ Réservation confirmée : {booking.reference} — {booking.room.property.name}"
    )
    context = {
        "booking":  booking,
        "site_url": _site_url(),
    }
    html_message = render_to_string("bookings/emails/confirmation.html", context)
    plain_message = (
        f"Bonjour {booking.guest_first_name} {booking.guest_last_name},\n\n"
        f"Votre réservation {booking.reference} est confirmée.\n\n"
        f"Établissement : {booking.room.property.name}\n"
        f"Chambre       : {booking.room.name}\n"
        f"Ville         : {booking.room.property.city.name}\n"
        f"Arrivée       : {booking.check_in.strftime('%d/%m/%Y')}\n"
        f"Départ        : {booking.check_out.strftime('%d/%m/%Y')}\n"
        f"Durée         : {booking.num_nights} nuit(s)\n"
        f"Total         : {booking.grand_total} MAD\n\n"
        f"Consultez vos réservations : {_site_url()}/traveler/bookings/\n\n"
        f"Merci de votre confiance,\nL'équipe RiadBook Maroc"
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.guest_email],
        html_message=html_message,
        fail_silently=False,
    )