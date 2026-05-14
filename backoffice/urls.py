from django.urls import path
from . import views

app_name = "backoffice"

urlpatterns = [
    path("",                                views.dashboard_view,          name="dashboard"),
    path("users/",                          views.users_view,              name="users"),
    path("users/<int:user_id>/toggle/",     views.user_toggle_active_view, name="user_toggle"),
    path("properties/",                     views.properties_view,         name="properties"),
    path("properties/<int:property_id>/action/", views.property_action_view, name="property_action"),
    path("reviews/",                        views.reviews_view,            name="reviews"),
    path("reviews/<int:review_id>/action/", views.review_action_view,      name="review_action"),
    path("bookings/",                       views.bookings_view,           name="bookings"),
    path("messages/",                       views.messaging_view,          name="messaging"),
    path("messages/<int:conversation_id>/", views.conversation_view,       name="conversation"),
    path("stats/",                          views.stats_view,              name="stats"),
]
