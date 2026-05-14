from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("book/<int:room_id>/",           views.booking_start_view,       name="start"),
    path("book/<int:room_id>/confirm/",   views.booking_confirm_view,     name="confirm"),
    path("voucher/<str:reference>/",      views.booking_voucher_view,     name="voucher"),
    path("cancel/<str:reference>/",       views.booking_cancel_view,      name="cancel"),
    path("check-availability/",           views.check_availability_view,  name="check_availability"),
    path("favorite/<int:property_id>/",   views.toggle_favorite_view,     name="toggle_favorite"),
]