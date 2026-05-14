from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from properties.models import Room
import uuid


class Availability(models.Model):
    room         = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="availability_entries")
    date         = models.DateField()
    is_available = models.BooleanField(default=True)
    note         = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table        = "availability"
        unique_together = [("room", "date")]
        indexes         = [models.Index(fields=["room", "date"])]

    def __str__(self): return f"{self.room} — {self.date} — {'✓' if self.is_available else '✗'}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING   = "pending",   _("En attente")
        CONFIRMED = "confirmed", _("Confirmé")
        CANCELLED = "cancelled", _("Annulé")
        COMPLETED = "completed", _("Séjour terminé")
        NO_SHOW   = "no_show",   _("Non présenté")

    reference   = models.CharField(max_length=12, unique=True, editable=False)
    traveler    = models.ForeignKey(User, on_delete=models.PROTECT, related_name="bookings",
                                    limit_choices_to={"role": "traveler"})
    room        = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="bookings")

    check_in    = models.DateField()
    check_out   = models.DateField()
    num_nights  = models.PositiveSmallIntegerField(editable=False)

    num_adults   = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    num_children = models.PositiveSmallIntegerField(default=0)

    price_per_night = models.DecimalField(max_digits=8,  decimal_places=2)
    total_price     = models.DecimalField(max_digits=10, decimal_places=2)
    taxes           = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    grand_total     = models.DecimalField(max_digits=10, decimal_places=2)

    guest_first_name = models.CharField(max_length=100)
    guest_last_name  = models.CharField(max_length=100)
    guest_email      = models.EmailField()
    guest_phone      = models.CharField(max_length=20, blank=True)
    special_requests = models.TextField(blank=True)

    status              = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    cancellation_reason = models.TextField(blank=True)
    cancelled_at        = models.DateTimeField(null=True, blank=True)
    cancelled_by        = models.ForeignKey(User, null=True, blank=True,
                            on_delete=models.SET_NULL, related_name="cancellations_made")

    confirmation_sent = models.BooleanField(default=False)
    voucher_sent      = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        indexes  = [
            models.Index(fields=["traveler", "status"]),
            models.Index(fields=["room", "check_in", "check_out"]),
            models.Index(fields=["reference"]),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self._generate_reference()
        if self.check_in and self.check_out:
            self.num_nights = (self.check_out - self.check_in).days
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_reference():
        return "RB" + uuid.uuid4().hex[:8].upper()

    def __str__(self): return f"Réservation {self.reference} — {self.traveler.full_name}"


class Favorite(models.Model):
    traveler   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites",
                                   limit_choices_to={"role": "traveler"})
    property   = models.ForeignKey("properties.Property", on_delete=models.CASCADE,
                                   related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = "favorites"
        unique_together = [("traveler", "property")]
