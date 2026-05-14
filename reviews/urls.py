from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path("property/<int:property_id>/reviews/", views.property_reviews_view, name="property_reviews"),
]
