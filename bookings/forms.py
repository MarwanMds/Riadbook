from django import forms
from datetime import date


class BookingForm(forms.Form):
    check_in  = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    num_adults   = forms.IntegerField(min_value=1, max_value=20, initial=1)
    num_children = forms.IntegerField(min_value=0, max_value=10, initial=0, required=False)
    guest_first_name = forms.CharField(max_length=100)
    guest_last_name  = forms.CharField(max_length=100)
    guest_email      = forms.EmailField()
    guest_phone      = forms.CharField(max_length=20, required=False)
    special_requests = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def clean(self):
        cleaned = super().clean()
        ci = cleaned.get("check_in")
        co = cleaned.get("check_out")
        if ci and co:
            if ci < date.today():
                raise forms.ValidationError("La date d'arrivée ne peut pas être dans le passé.")
            if co <= ci:
                raise forms.ValidationError("La date de départ doit être après la date d'arrivée.")
            if (co - ci).days > 30:
                raise forms.ValidationError("La durée maximale de séjour est de 30 nuits.")
        return cleaned