from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from properties.models import Property
from bookings.models import Booking


class Review(models.Model):
    class Status(models.TextChoices):
        PENDING  = "pending",  _("En attente de modération")
        APPROVED = "approved", _("Approuvé")
        REJECTED = "rejected", _("Rejeté")

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reviews")
    author   = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews",
                                 limit_choices_to={"role": "traveler"})
    booking  = models.OneToOneField(Booking, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="review")

    rating_overall     = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    rating_cleanliness = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    rating_location    = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    rating_value       = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    rating_service     = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)

    title   = models.CharField(max_length=150, blank=True)
    comment = models.TextField()

    is_verified     = models.BooleanField(default=False)
    status          = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    moderation_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "reviews"
        unique_together = [("property", "author")]
        indexes         = [
            models.Index(fields=["property", "status"]),
            models.Index(fields=["author"]),
        ]

    def save(self, *args, **kwargs):
        if self.booking and self.booking.status == "completed":
            self.is_verified = True
        super().save(*args, **kwargs)

    def __str__(self): return f"Avis {self.pk} — {self.author.full_name} → {self.property.name}"


class OwnerReply(models.Model):
    review     = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="owner_reply")
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner_replies",
                                   limit_choices_to={"role": "owner"})
    comment    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "owner_replies"

    def __str__(self): return f"Réponse de {self.author.full_name} à l'avis {self.review_id}"
