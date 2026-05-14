from django.shortcuts import render
from properties.models import Property, City
from django.db.models import Min


def home(request):
    featured = Property.objects.filter(
        status="approved"
    ).select_related("city").prefetch_related("photos").annotate(
        min_price=Min("rooms__price_per_night")
    ).order_by("-is_authentic_riad", "-avg_rating")[:6]

    cities = City.objects.filter(is_active=True).order_by("name")

    return render(request, "public/home.html", {
        "featured_properties": featured,
        "cities": cities,
    })
