from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import date, timedelta

from properties.models import Property, Room, PropertyPhoto, RoomPhoto
from bookings.models import Booking, Availability
from reviews.models import Review
from messaging.models import Conversation, Message as ConvMessage
from messaging.emails import send_new_message_notification


def _owner_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_owner:
            messages.error(request, "Accès réservé aux hôteliers.")
            return redirect("public:home")
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_owner_property(request, property_id):
    return get_object_or_404(Property, pk=property_id, owner=request.user)


# ── Dashboard ──────────────────────────────────────────────────────────────

@_owner_required
def dashboard_view(request):
    properties = Property.objects.filter(owner=request.user)
    prop_ids   = properties.values_list("id", flat=True)
    today      = date.today()
    month_start = today.replace(day=1)

    stats = {
        "total_properties": properties.count(),
        "approved":  properties.filter(status="approved").count(),
        "pending":   properties.filter(status="pending").count(),
        "bookings_total": Booking.objects.filter(room__property__in=prop_ids).count(),
        "bookings_month": Booking.objects.filter(
            room__property__in=prop_ids,
            created_at__date__gte=month_start
        ).count(),
        "revenue_month": Booking.objects.filter(
            room__property__in=prop_ids,
            status=Booking.Status.CONFIRMED,
            created_at__date__gte=month_start
        ).aggregate(t=Sum("grand_total"))["t"] or 0,
        "pending_reviews": Review.objects.filter(
            property__in=prop_ids, status="approved",
            owner_reply__isnull=True,
        ).count(),
    }

    upcoming = Booking.objects.filter(
        room__property__in=prop_ids,
        status=Booking.Status.CONFIRMED,
        check_in__gte=today,
    ).select_related("room__property", "traveler").order_by("check_in")[:5]

    recent_bookings = Booking.objects.filter(
        room__property__in=prop_ids,
    ).select_related("room__property").order_by("-created_at")[:6]

    return render(request, "owner/dashboard.html", {
        "properties":      properties,
        "stats":           stats,
        "upcoming":        upcoming,
        "recent_bookings": recent_bookings,
    })


# ── Properties ─────────────────────────────────────────────────────────────

@_owner_required
def properties_view(request):
    properties = Property.objects.filter(
        owner=request.user
    ).select_related("city").order_by("-created_at")
    return render(request, "owner/properties.html", {"properties": properties})


@_owner_required
def property_edit_view(request, property_id=None):
    from properties.forms import PropertyForm
    from properties.models import City, Amenity

    prop = _get_owner_property(request, property_id) if property_id else None

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=prop)
        if form.is_valid():
            p = form.save(commit=False)
            p.owner = request.user
            if not prop:
                p.status = Property.Status.PENDING
            p.save()
            form.save_m2m()
            cover = request.FILES.get("cover_photo")
            if cover:
                PropertyPhoto.objects.create(property=p, image=cover, is_cover=True)
            for f in request.FILES.getlist("photos"):
                PropertyPhoto.objects.create(property=p, image=f)
            action = "créé et soumis pour validation" if not prop else "mis à jour"
            messages.success(request, f"Établissement « {p.name} » {action}.")
            return redirect("owner:rooms", property_id=p.id)
    else:
        form = PropertyForm(instance=prop)

    return render(request, "owner/property_form.html", {
        "form":      form,
        "prop":      prop,
        "cities":    City.objects.filter(is_active=True).order_by("name"),
        "amenities": Amenity.objects.all().order_by("name"),
        "action":    "edit" if prop else "create",
    })


@_owner_required
def property_delete_view(request, property_id):
    prop = _get_owner_property(request, property_id)
    if request.method == "POST":
        name = prop.name
        prop.delete()
        messages.success(request, f"Établissement « {name} » supprimé.")
        return redirect("owner:properties")
    return render(request, "owner/property_delete_confirm.html", {"prop": prop})


# ── Rooms ──────────────────────────────────────────────────────────────────

@_owner_required
def rooms_view(request, property_id):
    prop  = _get_owner_property(request, property_id)
    rooms = prop.rooms.order_by("name")
    return render(request, "owner/rooms.html", {"prop": prop, "rooms": rooms})


@_owner_required
def room_edit_view(request, property_id, room_id=None):
    from properties.forms import RoomForm
    prop = _get_owner_property(request, property_id)
    room = get_object_or_404(Room, pk=room_id, property=prop) if room_id else None

    if request.method == "POST":
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            r = form.save(commit=False)
            r.property = prop
            r.save()
            for f in request.FILES.getlist("photos"):
                RoomPhoto.objects.create(room=r, image=f)
            action = "créée" if not room else "mise à jour"
            messages.success(request, f"Chambre « {r.name} » {action}.")
            return redirect("owner:rooms", property_id=prop.id)
    else:
        form = RoomForm(instance=room)

    return render(request, "owner/room_form.html", {
        "form": form, "prop": prop, "room": room,
    })


@_owner_required
def room_toggle_view(request, property_id, room_id):
    prop = _get_owner_property(request, property_id)
    room = get_object_or_404(Room, pk=room_id, property=prop)
    room.is_active = not room.is_active
    room.save(update_fields=["is_active"])
    messages.success(request, f"Chambre « {room.name} » {'activée' if room.is_active else 'désactivée'}.")
    return redirect("owner:rooms", property_id=prop.id)


# ── Availability ───────────────────────────────────────────────────────────

@_owner_required
def availability_view(request, property_id):
    prop      = _get_owner_property(request, property_id)
    rooms     = prop.rooms.filter(is_active=True)
    today     = date.today()
    days_list = [today + timedelta(days=i) for i in range(30)]

    blocked = {}
    for room in rooms:
        blocked[room.id] = set(
            Availability.objects.filter(
                room=room,
                date__range=(today, today + timedelta(days=29)),
                is_available=False,
            ).values_list("date", flat=True)
        )

    if request.method == "POST":
        room_id  = request.POST.get("room_id")
        date_str = request.POST.get("date")
        action   = request.POST.get("action")
        room = get_object_or_404(Room, pk=room_id, property=prop)
        d = date.fromisoformat(date_str)
        if action == "block":
            Availability.objects.update_or_create(
                room=room, date=d,
                defaults={"is_available": False, "note": "Bloqué par hôtelier"},
            )
        elif action == "unblock":
            Availability.objects.filter(room=room, date=d).delete()
        return redirect("owner:availability", property_id=prop.id)

    return render(request, "owner/availability.html", {
        "prop": prop, "rooms": rooms,
        "days_list": days_list, "blocked": blocked,
    })


# ── Bookings ───────────────────────────────────────────────────────────────

@_owner_required
def bookings_view(request):
    prop_ids = Property.objects.filter(owner=request.user).values_list("id", flat=True)
    status   = request.GET.get("status", "")
    bookings = Booking.objects.filter(
        room__property__in=prop_ids
    ).select_related("room__property", "traveler").order_by("-created_at")
    if status:
        bookings = bookings.filter(status=status)
    return render(request, "owner/bookings.html", {
        "bookings": bookings, "status_filter": status,
        "status_choices": Booking.Status.choices,
    })


@_owner_required
def booking_detail_view(request, reference):
    prop_ids = Property.objects.filter(owner=request.user).values_list("id", flat=True)
    booking  = get_object_or_404(Booking, reference=reference, room__property__in=prop_ids)
    return render(request, "owner/booking_detail.html", {"booking": booking})


# ── Reviews ────────────────────────────────────────────────────────────────

@_owner_required
def reviews_view(request):
    prop_ids = Property.objects.filter(owner=request.user).values_list("id", flat=True)
    reviews  = Review.objects.filter(
        property__in=prop_ids, status="approved",
    ).select_related("author", "property").order_by("-created_at")
    return render(request, "owner/reviews.html", {"reviews": reviews})


@_owner_required
def review_reply_view(request, review_id):
    from reviews.models import OwnerReply
    prop_ids = Property.objects.filter(owner=request.user).values_list("id", flat=True)
    review   = get_object_or_404(Review, pk=review_id, property__in=prop_ids)

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            OwnerReply.objects.update_or_create(
                review=review,
                defaults={"comment": body, "author": request.user},
            )
            messages.success(request, "Réponse publiée.")
        return redirect("owner:reviews")

    return render(request, "owner/review_reply.html", {"review": review})

# ── Messaging (Owner) ──────────────────────────────────────────────────────
 
@_owner_required
def messaging_view(request):
    conversations = Conversation.objects.filter(
        owner=request.user
    ).select_related("traveler", "property").prefetch_related(
        "messages"
    ).order_by("-last_message_at")
 
    return render(request, "owner/messaging.html", {
        "conversations": conversations,
    })
 
 
@_owner_required
def conversation_view(request, conversation_id):
    conversation = get_object_or_404(
        Conversation, pk=conversation_id, owner=request.user
    )
 
    # Mark traveler messages as read
    conversation.messages.filter(
        sender_type=ConvMessage.SenderType.TRAVELER, is_read=False
    ).update(is_read=True)
    conversation.unread_by_owner = 0
    conversation.save(update_fields=["unread_by_owner"])
 
    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            msg = ConvMessage.objects.create(
                conversation=conversation,
                sender=request.user,
                sender_type=ConvMessage.SenderType.OWNER,
                body=body,
            )
            conversation.last_message_at     = timezone.now()
            conversation.unread_by_traveler += 1
            conversation.save(update_fields=["last_message_at", "unread_by_traveler"])
            try:
                send_new_message_notification(msg)
            except Exception:
                pass
        # Pas de messages.success() — redirect silencieux
        return redirect("owner:conversation", conversation_id=conversation_id)
 
    # ✅ RENOMMÉ : "messages" → "chat_messages"
    chat_messages = conversation.messages.select_related("sender").order_by("created_at")
    return render(request, "owner/conversation.html", {
        "conversation":  conversation,
        "chat_messages": chat_messages,  # ← FIX ICI
    })