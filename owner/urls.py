from django.urls import path
from . import views

app_name = "owner"

urlpatterns = [
    path("",                                            views.dashboard_view,      name="dashboard"),
    path("properties/",                                 views.properties_view,     name="properties"),
    path("properties/new/",                             views.property_edit_view,  name="property_new"),
    path("properties/<int:property_id>/edit/",          views.property_edit_view,  name="property_edit"),
    path("properties/<int:property_id>/rooms/",         views.rooms_view,          name="rooms"),
    path("properties/<int:property_id>/rooms/new/",     views.room_edit_view,      name="room_new"),
    path("properties/<int:property_id>/rooms/<int:room_id>/edit/",   views.room_edit_view,   name="room_edit"),
    path("properties/<int:property_id>/rooms/<int:room_id>/toggle/", views.room_toggle_view, name="room_toggle"),
    path("properties/<int:property_id>/delete/",        views.property_delete_view, name="property_delete"),
    path("properties/<int:property_id>/availability/",  views.availability_view,    name="availability"),
    path("bookings/",                                   views.bookings_view,        name="bookings"),
    path("bookings/<str:reference>/",                   views.booking_detail_view,  name="booking_detail"),
    path("reviews/",                                    views.reviews_view,         name="reviews"),
    path("reviews/<int:review_id>/reply/",              views.review_reply_view,    name="review_reply"),

    # ── Messaging ──────────────────────────────────────────────────────────
    path("messages/",                                   views.messaging_view,       name="messaging"),
    path("messages/<int:conversation_id>/",             views.conversation_view,    name="conversation"),
]