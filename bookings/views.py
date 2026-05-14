from decimal import Decimal
from datetime import date, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from properties.models import Room, Property
from .models import Booking, Availability, Favorite
from .forms import BookingForm
from .emails import send_booking_confirmation

TAX_RATE = Decimal("0.10")


# ── Helpers ────────────────────────────────────────────────────────────────

def _is_room_available(room, check_in, check_out):
    dates_needed = []
    d = check_in
    while d < check_out:
        dates_needed.append(d)
        d += timedelta(days=1)
    blocked = Availability.objects.filter(
        room=room, date__in=dates_needed, is_available=False
    ).exists()
    return not blocked


def _block_dates(room, check_in, check_out, note="Booked"):
    d = check_in
    while d < check_out:
        Availability.objects.update_or_create(
            room=room, date=d,
            defaults={"is_available": False, "note": note},
        )
        d += timedelta(days=1)


def _unblock_dates(room, check_in, check_out):
    dates = []
    d = check_in
    while d < check_out:
        dates.append(d)
        d += timedelta(days=1)
    Availability.objects.filter(room=room, date__in=dates).delete()


def _compute_price(room, num_nights):
    subtotal    = room.price_per_night * num_nights
    taxes       = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
    grand_total = subtotal + taxes
    return subtotal, taxes, grand_total


# ── Step 1 — Show form ─────────────────────────────────────────────────────

@login_required
def booking_start_view(request, room_id):
    room     = get_object_or_404(Room, pk=room_id, is_active=True)
    property = room.property

    if property.status != "approved":
        messages.error(request, "Cet établissement n'est pas disponible.")
        return redirect("public:home")

    check_in_str  = request.GET.get("check_in", "")
    check_out_str = request.GET.get("check_out", "")
    guests        = int(request.GET.get("guests", 1))

    check_in = check_out = None
    num_nights = 0
    subtotal = taxes = grand_total = Decimal("0")

    try:
        check_in  = date.fromisoformat(check_in_str)
        check_out = date.fromisoformat(check_out_str)
        if check_out > check_in:
            num_nights = (check_out - check_in).days
            subtotal, taxes, grand_total = _compute_price(room, num_nights)
            if not _is_room_available(room, check_in, check_out):
                messages.warning(request,
                    "Cette chambre n'est plus disponible pour ces dates.")
                return redirect(
                    f"/property/{property.slug}/"
                    f"?check_in={check_in_str}&check_out={check_out_str}&guests={guests}"
                )
    except (ValueError, TypeError):
        pass

    initial = {
        "check_in":         check_in,
        "check_out":        check_out,
        "num_adults":       guests,
        "guest_first_name": request.user.first_name,
        "guest_last_name":  request.user.last_name,
        "guest_email":      request.user.email,
        "guest_phone":      request.user.phone,
    }
    form = BookingForm(initial=initial)

    return render(request, "bookings/booking_form.html", {
        "form": form, "room": room, "property": property,
        "check_in": check_in, "check_out": check_out,
        "num_nights": num_nights, "subtotal": subtotal,
        "taxes": taxes, "grand_total": grand_total,
    })


# ── Step 2 — Confirm & create ──────────────────────────────────────────────

@login_required
@require_POST
def booking_confirm_view(request, room_id):
    room     = get_object_or_404(Room, pk=room_id, is_active=True)
    property = room.property

    if property.status != "approved":
        messages.error(request, "Cet établissement n'est pas disponible.")
        return redirect("public:home")

    form = BookingForm(request.POST)

    if not form.is_valid():
        check_in  = form.data.get("check_in")
        check_out = form.data.get("check_out")
        num_nights = 0
        subtotal = taxes = grand_total = Decimal("0")
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
            if co > ci:
                num_nights = (co - ci).days
                subtotal, taxes, grand_total = _compute_price(room, num_nights)
        except (ValueError, TypeError):
            pass
        return render(request, "bookings/booking_form.html", {
            "form": form, "room": room, "property": property,
            "check_in": check_in, "check_out": check_out,
            "num_nights": num_nights, "subtotal": subtotal,
            "taxes": taxes, "grand_total": grand_total,
        })

    d          = form.cleaned_data
    check_in   = d["check_in"]
    check_out  = d["check_out"]
    num_nights = (check_out - check_in).days
    subtotal, taxes, grand_total = _compute_price(room, num_nights)

    # Race-condition guard
    if not _is_room_available(room, check_in, check_out):
        messages.error(request,
            "Désolé, cette chambre vient d'être réservée. "
            "Veuillez choisir d'autres dates.")
        return redirect(
            f"/property/{property.slug}/"
            f"?check_in={check_in}&check_out={check_out}"
        )

    with transaction.atomic():
        booking = Booking.objects.create(
            traveler         = request.user,
            room             = room,
            check_in         = check_in,
            check_out        = check_out,
            num_adults       = d["num_adults"],
            num_children     = d.get("num_children") or 0,
            price_per_night  = room.price_per_night,
            total_price      = subtotal,
            taxes            = taxes,
            grand_total      = grand_total,
            guest_first_name = d["guest_first_name"],
            guest_last_name  = d["guest_last_name"],
            guest_email      = d["guest_email"],
            guest_phone      = d.get("guest_phone", ""),
            special_requests = d.get("special_requests", ""),
            status           = Booking.Status.CONFIRMED,
        )
        _block_dates(room, check_in, check_out, note=f"Booked {booking.reference}")

    try:
        send_booking_confirmation(booking)
        booking.confirmation_sent = True
        booking.save(update_fields=["confirmation_sent"])
    except Exception:
        pass

    return redirect("bookings:voucher", reference=booking.reference)


# ── Voucher ────────────────────────────────────────────────────────────────

@login_required
def booking_voucher_view(request, reference):
    booking = get_object_or_404(Booking, reference=reference, traveler=request.user)
    return render(request, "bookings/voucher.html", {"booking": booking})


# ── Cancel ─────────────────────────────────────────────────────────────────

@login_required
def booking_cancel_view(request, reference):
    booking = get_object_or_404(Booking, reference=reference, traveler=request.user)

    if booking.status not in (Booking.Status.PENDING, Booking.Status.CONFIRMED):
        messages.error(request, "Cette réservation ne peut plus être annulée.")
        return redirect("traveler:reservations")

    if request.method == "POST":
        reason = request.POST.get("reason", "").strip()
        with transaction.atomic():
            booking.status              = Booking.Status.CANCELLED
            booking.cancellation_reason = reason
            booking.cancelled_at        = timezone.now()
            booking.cancelled_by        = request.user
            booking.save(update_fields=[
                "status", "cancellation_reason", "cancelled_at", "cancelled_by"
            ])
            _unblock_dates(booking.room, booking.check_in, booking.check_out)

        messages.success(request,
            f"Réservation {booking.reference} annulée.")
        return redirect("traveler:reservations")

    return render(request, "bookings/cancel_confirm.html", {"booking": booking})


# ── AJAX availability check ────────────────────────────────────────────────

def check_availability_view(request):
    room_id   = request.GET.get("room_id")
    check_in  = request.GET.get("check_in")
    check_out = request.GET.get("check_out")

    if not all([room_id, check_in, check_out]):
        return JsonResponse({"available": False, "error": "Paramètres manquants"})

    try:
        room = get_object_or_404(Room, pk=room_id, is_active=True)
        ci   = date.fromisoformat(check_in)
        co   = date.fromisoformat(check_out)
        if co <= ci:
            return JsonResponse({"available": False, "error": "Dates invalides"})

        num_nights = (co - ci).days
        available  = _is_room_available(room, ci, co)
        subtotal, taxes, grand_total = _compute_price(room, num_nights)

        return JsonResponse({
            "available":   available,
            "num_nights":  num_nights,
            "subtotal":    float(subtotal),
            "taxes":       float(taxes),
            "grand_total": float(grand_total),
        })
    except (ValueError, TypeError):
        return JsonResponse({"available": False, "error": "Dates invalides"})


# ── Toggle favorite ────────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_favorite_view(request, property_id):
    if not request.user.is_traveler:
        return JsonResponse({"error": "Réservé aux voyageurs"}, status=403)

    property = get_object_or_404(Property, pk=property_id, status="approved")
    fav, created = Favorite.objects.get_or_create(
        traveler=request.user, property=property
    )
    if not created:
        fav.delete()
        is_favorite = False
    else:
        is_favorite = True

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"is_favorite": is_favorite})

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)
