from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Review
from properties.models import Property


def property_reviews_view(request, property_id):
    """Public list of approved reviews for a property."""
    property = get_object_or_404(Property, pk=property_id, status="approved")
    reviews = Review.objects.filter(
        property=property, status=Review.Status.APPROVED
    ).select_related("author").order_by("-created_at")
    return render(request, "reviews/property_reviews.html", {
        "property": property,
        "reviews":  reviews,
    })