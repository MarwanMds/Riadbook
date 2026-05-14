from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from accounts.models import User


class City(models.Model):
    name       = models.CharField(max_length=100)
    name_ar    = models.CharField(max_length=100, blank=True)
    name_en    = models.CharField(max_length=100, blank=True)
    slug       = models.SlugField(unique=True)
    latitude   = models.DecimalField(max_digits=9, decimal_places=6)
    longitude  = models.DecimalField(max_digits=9, decimal_places=6)
    is_active  = models.BooleanField(default=True)
    image      = models.ImageField(upload_to="cities/", null=True, blank=True)

    class Meta:
        db_table            = "cities"
        verbose_name        = _("Ville")
        verbose_name_plural = _("Villes")

    def __str__(self): return self.name

    def get_translated_name(self, lang_code):
        """Return the name in the requested language if available."""
        if lang_code == 'ar' and self.name_ar:
            return self.name_ar
        if lang_code == 'en' and self.name_en:
            return self.name_en
        return self.name


class Amenity(models.Model):
    name     = models.CharField(max_length=80, unique=True)
    name_ar  = models.CharField(max_length=80, blank=True)
    name_en  = models.CharField(max_length=80, blank=True)
    icon     = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table            = "amenities"
        verbose_name        = _("Équipement")
        verbose_name_plural = _("Équipements")

    def __str__(self): return self.name

    def get_translated_name(self, lang_code):
        if lang_code == 'ar' and self.name_ar:
            return self.name_ar
        if lang_code == 'en' and self.name_en:
            return self.name_en
        return self.name


class Property(models.Model):
    class PropertyType(models.TextChoices):
        HOTEL       = "hotel",       _("Hôtel")
        RIAD        = "riad",        _("Riad")
        GUESTHOUSE  = "guesthouse",  _("Maison d'hôtes")

    class Style(models.TextChoices):
        TRADITIONAL = "traditional", _("Traditionnel")
        MODERN      = "modern",      _("Moderne")
        LUXURY      = "luxury",      _("Luxe")
        BUDGET      = "budget",      _("Économique")

    class Status(models.TextChoices):
        PENDING   = "pending",   _("En attente de validation")
        APPROVED  = "approved",  _("Approuvé")
        REJECTED  = "rejected",  _("Rejeté")
        SUSPENDED = "suspended", _("Suspendu")

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="properties",
                              limit_choices_to={"role": "owner"})

    name          = models.CharField(max_length=200)
    slug          = models.SlugField(unique=True, max_length=220)
    description   = models.TextField()
    description_ar = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    property_type = models.CharField(max_length=15, choices=PropertyType.choices)
    style         = models.CharField(max_length=15, choices=Style.choices, default=Style.TRADITIONAL)

    city       = models.ForeignKey(City, on_delete=models.PROTECT, related_name="properties")
    address    = models.CharField(max_length=300)
    latitude   = models.DecimalField(max_digits=9,  decimal_places=6, null=True, blank=True)
    longitude  = models.DecimalField(max_digits=9,  decimal_places=6, null=True, blank=True)

    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")

    is_authentic_riad = models.BooleanField(default=False)
    free_cancellation = models.BooleanField(default=False)
    status            = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    avg_rating    = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    review_count  = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table            = "properties"
        verbose_name        = _("Établissement")
        verbose_name_plural = _("Établissements")
        indexes = [
            models.Index(fields=["city", "property_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["avg_rating"]),
        ]

    def __str__(self): return self.name


class PropertyPhoto(models.Model):
    property    = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="photos")
    image       = models.ImageField(upload_to="properties/%Y/%m/")
    caption     = models.CharField(max_length=200, blank=True)
    is_cover    = models.BooleanField(default=False)
    order       = models.PositiveSmallIntegerField(default=0)
    is_approved = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "property_photos"
        ordering = ["order", "-uploaded_at"]

    def __str__(self): return f"Photo {self.pk} — {self.property.name}"


class Room(models.Model):
    class BedType(models.TextChoices):
        SINGLE = "single", _("Lit simple")
        DOUBLE = "double", _("Lit double")
        TWIN   = "twin",   _("Lits jumeaux")
        SUITE  = "suite",  _("Suite")
        DORM   = "dorm",   _("Dortoir")

    class CancellationPolicy(models.TextChoices):
        FREE        = "free",        _("Annulation gratuite")
        MODERATE    = "moderate",    _("Politique modérée")
        STRICT      = "strict",      _("Non remboursable")

    property        = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="rooms")
    name            = models.CharField(max_length=150)
    description     = models.TextField(blank=True)
    bed_type        = models.CharField(max_length=10, choices=BedType.choices, default=BedType.DOUBLE)
    capacity        = models.PositiveSmallIntegerField(default=2,
                        validators=[MinValueValidator(1), MaxValueValidator(20)])
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2,
                        validators=[MinValueValidator(0)])

    free_cancellation     = models.BooleanField(default=False)
    cancellation_deadline = models.PositiveSmallIntegerField(default=0)
    cancellation_policy   = models.CharField(max_length=10, choices=CancellationPolicy.choices,
                              default=CancellationPolicy.STRICT, blank=True)

    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rooms"

    def __str__(self): return f"{self.name} — {self.property.name}"


class RoomPhoto(models.Model):
    room  = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="rooms/%Y/%m/")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "room_photos"
        ordering = ["order"]
