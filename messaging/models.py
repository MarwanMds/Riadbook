from django.db import models
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from properties.models import Property


class Conversation(models.Model):
    class Status(models.TextChoices):
        OPEN    = "open",    _("Ouvert")
        CLOSED  = "closed",  _("Fermé")
        PENDING = "pending", _("En attente")

    traveler = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="conversations",
        limit_choices_to={"role__in": ["traveler", "owner"]},
    )
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="owner_conversations",
        limit_choices_to={"role": "owner"},
    )
    property = models.ForeignKey(
        Property, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="conversations",
    )

    subject = models.CharField(max_length=200)
    status  = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    last_message_at    = models.DateTimeField(null=True, blank=True)
    unread_by_admin    = models.PositiveSmallIntegerField(default=0)
    unread_by_traveler = models.PositiveSmallIntegerField(default=0)
    unread_by_owner    = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-last_message_at"]

    def __str__(self): return f"Conv {self.pk}: {self.subject}"

    def is_owner_conversation(self):
        return self.owner_id is not None


class Message(models.Model):
    class SenderType(models.TextChoices):
        TRAVELER = "traveler", _("Voyageur")
        ADMIN    = "admin",    _("Administrateur")
        OWNER    = "owner",    _("Hôtelier")

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sent_messages")
    sender_type  = models.CharField(max_length=10, choices=SenderType.choices)
    body         = models.TextField()
    is_read      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]

    def __str__(self): return f"Msg {self.pk} in conv {self.conversation_id}"


class Notification(models.Model):
    class NotifType(models.TextChoices):
        BOOKING_CONFIRMED = "booking_confirmed", _("Réservation confirmée")
        BOOKING_CANCELLED = "booking_cancelled", _("Réservation annulée")
        NEW_MESSAGE       = "new_message",       _("Nouveau message")
        REVIEW_POSTED     = "review_posted",     _("Nouvel avis")
        LISTING_APPROVED  = "listing_approved",  _("Établissement approuvé")
        LISTING_REJECTED  = "listing_rejected",  _("Établissement rejeté")

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=25, choices=NotifType.choices)
    title      = models.CharField(max_length=150)
    body       = models.TextField(blank=True)
    link       = models.CharField(max_length=300, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
