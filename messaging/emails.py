from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _site_url():
    return getattr(settings, "SITE_URL", "https://www.riadbook.ma")


def _reply_url(recipient, conversation):
    """Build the correct reply URL based on the recipient's role."""
    base = _site_url()
    role = recipient.role
    conv_id = conversation.pk

    if role == "traveler":
        return f"{base}/traveler/messaging/{conv_id}/"
    elif role == "owner":
        return f"{base}/owner/messaging/{conv_id}/"
    else:
        # admin
        return f"{base}/backoffice/messaging/{conv_id}/"


def send_new_message_notification(message):
    """
    Email 3 — New message notification.
    Sent to the recipient(s) of a conversation when a new message arrives.

    Recipient logic:
      - If sender is the traveler  → notify the owner (or admin if no owner)
      - If sender is the owner     → notify the traveler
      - If sender is admin         → notify the traveler (and owner if present)
    """
    conversation = message.conversation
    sender = message.sender

    # Build preview (max 300 chars, no HTML)
    preview = message.body[:300] + ("…" if len(message.body) > 300 else "")

    def _notify(recipient):
        if not recipient or recipient == sender:
            return
        context = {
            "recipient":       recipient,
            "sender":          sender,
            "conversation":    conversation,
            "message":         message,
            "message_preview": preview,
            "reply_url":       _reply_url(recipient, conversation),
            "site_url":        _site_url(),
        }
        subject = f"💬 Nouveau message : {conversation.subject} — RiadBook Maroc"
        html_message = render_to_string("messaging/emails/new_message.html", context)
        plain_message = (
            f"Bonjour {recipient.first_name},\n\n"
            f"Vous avez reçu un nouveau message de {sender.get_full_name()} "
            f"concernant : « {conversation.subject} ».\n\n"
            f"Extrait : {preview}\n\n"
            f"Répondre : {_reply_url(recipient, conversation)}\n\n"
            f"L'équipe RiadBook Maroc"
        )
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            html_message=html_message,
            fail_silently=False,
        )

    if sender == conversation.traveler:
        # Traveler sent → notify owner or admin
        _notify(conversation.owner)
        if not conversation.owner:
            # General inquiry → notify admin users
            from accounts.models import User
            for admin in User.objects.filter(role="admin", is_active=True):
                _notify(admin)

    elif sender == conversation.owner:
        # Owner replied → notify traveler
        _notify(conversation.traveler)

    else:
        # Admin sent → notify traveler (and owner if present)
        _notify(conversation.traveler)
        if conversation.owner:
            _notify(conversation.owner)
