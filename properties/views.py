from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Min
from .models import Property, City, Amenity, Room
from .forms import SearchForm, FilterForm
from bookings.models import Availability
from datetime import date, timedelta
import json


# ---------------------------------------------------------------------------
# Search & Results
# ---------------------------------------------------------------------------
def search_view(request):
    search_form = SearchForm(request.GET or None)
    filter_form = FilterForm(request.GET or None)

    properties = Property.objects.filter(status="approved").select_related(
        "city", "owner"
    ).prefetch_related("photos", "amenities")

    # ── Search params ──
    city_id   = request.GET.get("city")
    check_in  = request.GET.get("check_in")
    check_out = request.GET.get("check_out")
    guests    = request.GET.get("guests", 1)

    if city_id:
        properties = properties.filter(city_id=city_id)

    # Filter rooms by capacity & availability
    if check_in and check_out and guests:
        try:
            ci     = date.fromisoformat(check_in)
            co     = date.fromisoformat(check_out)
            guests = int(guests)

            # Get dates in range
            dates_needed = []
            d = ci
            while d < co:
                dates_needed.append(d)
                d += timedelta(days=1)

            # Properties that have at least one room with enough capacity
            # and no blocked dates in the range
            blocked_room_ids = Availability.objects.filter(
                date__in=dates_needed,
                is_available=False,
            ).values_list("room_id", flat=True)

            available_room_ids = Room.objects.filter(
                property__in=properties,
                capacity__gte=guests,
                is_active=True,
            ).exclude(id__in=blocked_room_ids).values_list("property_id", flat=True)

            properties = properties.filter(id__in=available_room_ids)
        except (ValueError, TypeError):
            pass

    # ── Filters ──
    if filter_form.is_valid():
        d = filter_form.cleaned_data

        if d.get("property_type"):
            properties = properties.filter(property_type=d["property_type"])

        if d.get("style"):
            properties = properties.filter(style=d["style"])

        if d.get("price_min") is not None:
            properties = properties.filter(
                rooms__price_per_night__gte=d["price_min"]
            )
        if d.get("price_max") is not None:
            properties = properties.filter(
                rooms__price_per_night__lte=d["price_max"]
            )
        if d.get("rating_min"):
            properties = properties.filter(avg_rating__gte=d["rating_min"])

        if d.get("amenities"):
            for amenity in d["amenities"]:
                properties = properties.filter(amenities=amenity)

        if d.get("free_cancellation"):
            properties = properties.filter(free_cancellation=True)

        if d.get("authentic_riad"):
            properties = properties.filter(is_authentic_riad=True)

        # ── Sort ──
        sort = d.get("sort", "recommended")
        if sort == "price_asc":
            properties = properties.annotate(
                min_price=Min("rooms__price_per_night")
            ).order_by("min_price")
        elif sort == "price_desc":
            properties = properties.annotate(
                min_price=Min("rooms__price_per_night")
            ).order_by("-min_price")
        elif sort == "rating":
            properties = properties.order_by("-avg_rating")
        else:
            properties = properties.order_by("-is_authentic_riad", "-avg_rating")

    properties = properties.distinct()

    # Attach min price for display
    properties = properties.annotate(min_price=Min("rooms__price_per_night"))

    # Map data (for Leaflet)
    map_data = [
        {
            "id":   p.id,
            "name": p.name,
            "lat":  float(p.latitude)  if p.latitude  else None,
            "lng":  float(p.longitude) if p.longitude else None,
            "slug": p.slug,
            "type": p.property_type,
            "price": float(p.min_price) if p.min_price else None,
            "rating": float(p.avg_rating),
        }
        for p in properties if p.latitude and p.longitude
    ]

    cities    = City.objects.filter(is_active=True).order_by("name")
    amenities = Amenity.objects.all()

    return render(request, "properties/search.html", {
        "properties":  properties,
        "search_form": search_form,
        "filter_form": filter_form,
        "map_data":    json.dumps(map_data),
        "cities":      cities,
        "amenities":   amenities,
        "total":       properties.count(),
        # Pass search params back to template
        "q_city":      city_id,
        "q_check_in":  check_in,
        "q_check_out": check_out,
        "q_guests":    guests,
    })


# ---------------------------------------------------------------------------
# Property Detail
# ---------------------------------------------------------------------------
def property_detail_view(request, slug):
    property = get_object_or_404(
        Property.objects.select_related("city", "owner")
                        .prefetch_related("photos", "amenities", "rooms__photos"),
        slug=slug,
        status="approved",
    )

    # Approved reviews
    reviews = property.reviews.filter(status="approved").select_related(
        "author"
    ).prefetch_related("owner_reply").order_by("-created_at")[:10]

    # Rooms with availability check
    check_in  = request.GET.get("check_in")
    check_out = request.GET.get("check_out")
    guests    = int(request.GET.get("guests", 1))

    rooms = property.rooms.filter(is_active=True, capacity__gte=guests)

    if check_in and check_out:
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
            dates_needed = []
            d = ci
            while d < co:
                dates_needed.append(d)
                d += timedelta(days=1)

            blocked = Availability.objects.filter(
                room__in=rooms,
                date__in=dates_needed,
                is_available=False,
            ).values_list("room_id", flat=True)

            rooms = rooms.exclude(id__in=blocked)

            # Compute total price per room
            num_nights = (co - ci).days
            rooms_with_price = []
            for room in rooms:
                rooms_with_price.append({
                    "room":        room,
                    "num_nights":  num_nights,
                    "total_price": room.price_per_night * num_nights,
                })
        except ValueError:
            rooms_with_price = [{"room": r, "num_nights": 1,
                                  "total_price": r.price_per_night} for r in rooms]
    else:
        rooms_with_price = [{"room": r, "num_nights": 1,
                              "total_price": r.price_per_night} for r in rooms]

    # Rating breakdown
    rating_breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in property.reviews.filter(status="approved"):
        rating_breakdown[review.rating_overall] = \
            rating_breakdown.get(review.rating_overall, 0) + 1

    return render(request, "properties/detail.html", {
        "property":         property,
        "rooms_with_price": rooms_with_price,
        "reviews":          reviews,
        "rating_breakdown": rating_breakdown,
        "check_in":         check_in,
        "check_out":        check_out,
        "guests":           guests,
    })


# ---------------------------------------------------------------------------
# Riad Showcase
# ---------------------------------------------------------------------------
def riad_showcase_view(request):
    city_slug = request.GET.get("city", "")
    riads = Property.objects.filter(
        status="approved",
        property_type="riad",
    ).select_related("city").prefetch_related("photos").annotate(
        min_price=Min("rooms__price_per_night")
    ).order_by("-is_authentic_riad", "-avg_rating")

    if city_slug:
        riads = riads.filter(city__slug=city_slug)

    cities = City.objects.filter(is_active=True).order_by("name")

    map_data = [
        {
            "id":    r.id,
            "name":  r.name,
            "lat":   float(r.latitude)  if r.latitude  else None,
            "lng":   float(r.longitude) if r.longitude else None,
            "slug":  r.slug,
            "city":  r.city.name,
            "auth":  r.is_authentic_riad,
            "price": float(r.min_price) if r.min_price else None,
        }
        for r in riads if r.latitude and r.longitude
    ]

    return render(request, "properties/riads.html", {
        "riads":     riads,
        "cities":    cities,
        "map_data": json.dumps(map_data),
        "city_slug": city_slug,
        "total":     riads.count(),
    })
