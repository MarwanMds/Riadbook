from django import forms
from datetime import date, timedelta
from .models import City, Property, Amenity, Room


class SearchForm(forms.Form):
    """Main search bar used on home + results pages."""
    city          = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True).order_by("name"),
        required=False,
        empty_label="Toutes les villes",
        widget=forms.Select(attrs={"class": "search-select"}),
    )
    check_in  = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=lambda: (date.today() + timedelta(days=1)).isoformat(),
    )
    check_out = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        initial=lambda: (date.today() + timedelta(days=3)).isoformat(),
    )
    guests = forms.IntegerField(
        required=False, min_value=1, max_value=30, initial=2,
        widget=forms.NumberInput(attrs={"min": 1, "max": 30}),
    )

    def clean(self):
        cleaned = super().clean()
        ci = cleaned.get("check_in")
        co = cleaned.get("check_out")
        if ci and co:
            if ci < date.today():
                self.add_error("check_in", "La date d'arrivée ne peut pas être dans le passé.")
            if co <= ci:
                self.add_error("check_out", "La date de départ doit être après l'arrivée.")
        return cleaned


class FilterForm(forms.Form):
    """Sidebar filters on the results page."""
    PROPERTY_TYPE_CHOICES = [
        ("", "Tous"),
        ("riad",       "Riad"),
        ("hotel",      "Hôtel"),
        ("guesthouse", "Maison d'hôtes"),
    ]
    STYLE_CHOICES = [
        ("", "Tous les styles"),
        ("traditional", "Traditionnel"),
        ("modern",      "Moderne"),
        ("luxury",      "Luxe"),
        ("budget",      "Économique"),
    ]
    SORT_CHOICES = [
        ("recommended", "Recommandés"),
        ("price_asc",   "Prix croissant"),
        ("price_desc",  "Prix décroissant"),
        ("rating",      "Meilleures notes"),
    ]

    property_type     = forms.ChoiceField(choices=PROPERTY_TYPE_CHOICES, required=False)
    style             = forms.ChoiceField(choices=STYLE_CHOICES, required=False)
    price_min         = forms.IntegerField(required=False, min_value=0)
    price_max         = forms.IntegerField(required=False, min_value=0)
    rating_min        = forms.IntegerField(required=False, min_value=1, max_value=5)
    amenities         = forms.ModelMultipleChoiceField(
        queryset=Amenity.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    free_cancellation = forms.BooleanField(required=False)
    authentic_riad    = forms.BooleanField(required=False)
    sort              = forms.ChoiceField(choices=SORT_CHOICES, required=False,
                                          initial="recommended")


class PropertyForm(forms.ModelForm):
    class Meta:
        model  = Property
        fields = [
            "name", "property_type", "style", "city", "address",
            "latitude", "longitude", "description",
            "amenities", "free_cancellation", "is_authentic_riad",
        ]
        widgets = {
            "name":        forms.TextInput(attrs={"placeholder": "Nom de l'établissement"}),
            "address":     forms.TextInput(attrs={"placeholder": "Adresse complète"}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "latitude":    forms.NumberInput(attrs={"step": "0.000001", "placeholder": "ex: 31.628674"}),
            "longitude":   forms.NumberInput(attrs={"step": "0.000001", "placeholder": "ex: -7.992047"}),
            "amenities":   forms.CheckboxSelectMultiple(),
        }
        labels = {
            "name":             "Nom de l'établissement *",
            "property_type":    "Type *",
            "style":            "Style *",
            "city":             "Ville *",
            "address":          "Adresse *",
            "latitude":         "Latitude",
            "longitude":        "Longitude",
            "description":      "Description *",
            "amenities":        "Équipements",
            "free_cancellation":"Annulation gratuite",
            "is_authentic_riad":"Label Riad Authentique",
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model  = Room
        fields = [
            "name", "bed_type", "capacity", "price_per_night",
            "description", "free_cancellation", "cancellation_deadline", "is_active",
        ]
        widgets = {
            "name":        forms.TextInput(attrs={"placeholder": "ex: Suite Royale"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "price_per_night": forms.NumberInput(attrs={"step": "0.01", "placeholder": "Prix en MAD"}),
        }
        labels = {
            "name":                 "Nom de la chambre *",
            "bed_type":             "Type de lit *",
            "capacity":             "Capacité (personnes) *",
            "price_per_night":      "Prix par nuit (MAD) *",
            "description":          "Description",
            "free_cancellation":    "Annulation gratuite",
            "cancellation_deadline":"Délai annulation (heures)",
            "is_active":            "Chambre active",
        }