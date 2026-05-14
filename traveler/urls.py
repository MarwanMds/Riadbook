from django.urls import path
from . import views

app_name = "traveler"

urlpatterns = [
    path("",                              views.dashboard_view,          name="dashboard"),
    path("reservations/",                 views.reservations_view,       name="reservations"),
    path("favorites/",                    views.favorites_view,          name="favorites"),
    path("reviews/",                      views.reviews_view,            name="reviews"),
    path("reviews/submit/<int:booking_id>/", views.submit_review_view,  name="submit_review"),
    path("messages/",                     views.messaging_view,          name="messaging"),
    path("messages/new/",                 views.new_conversation_view,   name="new_conversation"),
    path("messages/<int:conversation_id>/", views.conversation_view,     name="conversation"),
]
