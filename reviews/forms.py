from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model  = Review
        fields = [
            "rating_overall", "rating_cleanliness", "rating_location",
            "rating_value", "rating_service", "title", "comment",
        ]
        widgets = {
            "rating_overall":    forms.Select(choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)]),
            "rating_cleanliness": forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
            "rating_location":   forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
            "rating_value":      forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
            "rating_service":    forms.Select(choices=[(i, str(i)) for i in range(1, 6)]),
            "title":   forms.TextInput(attrs={"placeholder": "Résumez votre séjour en une phrase"}),
            "comment": forms.Textarea(attrs={"rows": 5, "placeholder": "Décrivez votre expérience..."}),
        }
        labels = {
            "rating_overall":    "Note globale *",
            "rating_cleanliness": "Propreté",
            "rating_location":   "Emplacement",
            "rating_value":      "Rapport qualité/prix",
            "rating_service":    "Service",
            "title":   "Titre de l'avis",
            "comment": "Votre avis *",
        }
