from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.utils import timezone

from bookings.models import Booking, Favorite
from reviews.models import Review
from messaging.models import Conversation
from messaging.emails import send_new_message_notification


def _traveler_required(view_func):
    """Decorator: user must be authenticated AND have role=traveler."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_traveler:
            messages.error(request, "Accès réservé aux voyageurs.")
            return redirect("public:home")
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Dashboard ──────────────────────────────────────────────────────────────

@_traveler_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    upcoming = Booking.objects.filter(
        traveler=user,
        status=Booking.Status.CONFIRMED,
        check_out__gte=today,
    ).select_related("room__property__city").order_by("check_in")[:3]

    recent = Booking.objects.filter(
        traveler=user,
    ).filter(
        models.Q(status=Booking.Status.COMPLETED) |
        models.Q(status=Booking.Status.CONFIRMED, check_out__lt=today)
    ).select_related("room__property").order_by("-check_out")[:3]

    pending_reviews = Booking.objects.filter(
        traveler=user,
    ).filter(
        models.Q(status=Booking.Status.COMPLETED) |
        models.Q(status=Booking.Status.CONFIRMED, check_out__lt=today)
    ).exclude(review__isnull=False).select_related("room__property")[:5]

    unread_messages = Conversation.objects.filter(
        traveler=user,
        unread_by_traveler__gt=0,
    ).count()

    stats = {
        "total_bookings": Booking.objects.filter(traveler=user).count(),
        "upcoming_count": Booking.objects.filter(
            traveler=user, status=Booking.Status.CONFIRMED
        ).count(),
        "favorites_count": Favorite.objects.filter(traveler=user).count(),
        "reviews_count":   Review.objects.filter(author=user).count(),
    }

    return render(request, "traveler/dashboard.html", {
        "upcoming":        upcoming,
        "recent":          recent,
        "pending_reviews": pending_reviews,
        "unread_messages": unread_messages,
        "stats":           stats,
    })


# ── Reservations ───────────────────────────────────────────────────────────

@_traveler_required
def reservations_view(request):
    status_filter = request.GET.get("status", "")
    bookings = Booking.objects.filter(
        traveler=request.user
    ).select_related(
        "room__property__city", "room__property"
    ).order_by("-created_at")

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    return render(request, "traveler/reservations.html", {
        "bookings":       bookings,
        "status_filter":  status_filter,
        "today":          timezone.now().date(),
        "status_choices": Booking.Status.choices,
    })


# ── Favorites ──────────────────────────────────────────────────────────────

@_traveler_required
def favorites_view(request):
    favorites = Favorite.objects.filter(
        traveler=request.user
    ).select_related(
        "property__city"
    ).prefetch_related(
        "property__photos"
    ).order_by("-created_at")

    return render(request, "traveler/favorites.html", {"favorites": favorites})


# ── Reviews ────────────────────────────────────────────────────────────────

@_traveler_required
def reviews_view(request):
    reviews = Review.objects.filter(
        author=request.user
    ).select_related("property__city").order_by("-created_at")

    today = timezone.now().date()

    # Bookings eligible for a review:
    # - status COMPLETED, OR
    # - status CONFIRMED with check_out already passed (stay is over)
    pending = Booking.objects.filter(
        traveler=request.user,
    ).filter(
        models.Q(status=Booking.Status.COMPLETED) |
        models.Q(status=Booking.Status.CONFIRMED, check_out__lt=today)
    ).exclude(
        review__isnull=False
    ).select_related("room__property")

    return render(request, "traveler/reviews.html", {
        "reviews": reviews,
        "pending": pending,
    })


@_traveler_required
def submit_review_view(request, booking_id):
    from reviews.models import Review
    from reviews.forms import ReviewForm

    today = timezone.now().date()

    # Accept COMPLETED bookings OR CONFIRMED bookings whose stay is over
    booking = get_object_or_404(
        Booking,
        pk=booking_id,
        traveler=request.user,
    )

    # Security: stay must actually be over
    if booking.status == Booking.Status.CANCELLED:
        messages.error(request, "Impossible de laisser un avis pour une réservation annulée.")
        return redirect("traveler:reviews")

    if booking.check_out >= today:
        messages.info(request, "Vous pourrez laisser un avis après votre séjour.")
        return redirect("traveler:reviews")

    # Auto-complete the booking if it's still CONFIRMED but stay is over
    if booking.status == Booking.Status.CONFIRMED and booking.check_out < today:
        booking.status = Booking.Status.COMPLETED
        booking.save(update_fields=["status"])

    if booking.status not in (Booking.Status.COMPLETED,):
        messages.error(request, "Ce séjour n'est pas éligible pour un avis.")
        return redirect("traveler:reviews")

    if Review.objects.filter(author=request.user, property=booking.room.property).exists():
        messages.info(request, "Vous avez déjà soumis un avis pour cet établissement.")
        return redirect("traveler:reviews")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review             = form.save(commit=False)
            review.property    = booking.room.property
            review.author      = request.user
            review.booking     = booking
            review.is_verified = True
            review.save()
            _update_property_rating(booking.room.property)
            messages.success(request, "Votre avis a été soumis et sera visible après modération. Merci !")
            return redirect("traveler:reviews")
    else:
        form = ReviewForm()

    return render(request, "traveler/submit_review.html", {
        "form":    form,
        "booking": booking,
    })


def _update_property_rating(property_obj):
    from reviews.models import Review
    agg = Review.objects.filter(
        property=property_obj, status="approved"
    ).aggregate(avg=models.Avg("rating_overall"), cnt=models.Count("id"))
    property_obj.avg_rating   = agg["avg"] or 0
    property_obj.review_count = agg["cnt"] or 0
    property_obj.save(update_fields=["avg_rating", "review_count"])


# ── Messaging ──────────────────────────────────────────────────────────────

@_traveler_required
def messaging_view(request):
    conversations = Conversation.objects.filter(
        traveler=request.user
    ).prefetch_related("messages").order_by("-last_message_at")

    return render(request, "traveler/messaging.html", {
        "conversations": conversations,
    })


@_traveler_required
def conversation_view(request, conversation_id):
    from messaging.models import Message
    from django.utils import timezone

    conversation = get_object_or_404(
        Conversation, pk=conversation_id, traveler=request.user
    )

    # Mark owner/admin messages as read
    conversation.messages.filter(
        sender_type__in=[Message.SenderType.ADMIN, Message.SenderType.OWNER],
        is_read=False,
    ).update(is_read=True)
    conversation.unread_by_traveler = 0
    conversation.save(update_fields=["unread_by_traveler"])

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                sender_type=Message.SenderType.TRAVELER,
                body=body,
            )
            conversation.last_message_at  = timezone.now()
            conversation.unread_by_admin += 1
            if conversation.owner:
                conversation.unread_by_owner += 1
            conversation.save(update_fields=["last_message_at", "unread_by_admin", "unread_by_owner"])
            try:
                send_new_message_notification(msg)
            except Exception:
                pass  # Never let email failure break the chat
        # Pas de messages.success() — redirect silencieux
        return redirect("traveler:conversation", conversation_id=conversation_id)

    # ✅ RENOMMÉ : "messages" → "chat_messages" pour ne pas écraser le context processor Django
    chat_messages = conversation.messages.select_related("sender").order_by("created_at")
    return render(request, "traveler/conversation.html", {
        "conversation":  conversation,
        "chat_messages": chat_messages,  # ← FIX ICI
    })


@_traveler_required
def new_conversation_view(request):
    from messaging.models import Message
    from properties.models import Property
    from django.utils import timezone

    if request.method == "POST":
        subject     = request.POST.get("subject", "").strip()
        body        = request.POST.get("body", "").strip()
        property_id = request.POST.get("property_id")

        if not subject or not body:
            messages.error(request, "Sujet et message sont obligatoires.")
        else:
            property_obj = None
            owner_obj    = None

            if property_id:
                property_obj = Property.objects.filter(
                    pk=property_id, status="approved"
                ).select_related("owner").first()
                if property_obj:
                    owner_obj = property_obj.owner

            conv = Conversation.objects.create(
                traveler        = request.user,
                property        = property_obj,
                owner           = owner_obj,
                subject         = subject,
                unread_by_owner = 1 if owner_obj else 0,
                unread_by_admin = 0 if owner_obj else 1,
                last_message_at = timezone.now(),
            )
            Message.objects.create(
                conversation=conv,
                sender=request.user,
                sender_type=Message.SenderType.TRAVELER,
                body=body,
            )
            try:
                send_new_message_notification(
                    conv.messages.select_related("sender", "conversation__traveler",
                                                 "conversation__owner").last()
                )
            except Exception:
                pass
            # Pas de messages.success() ici non plus
            return redirect("traveler:conversation", conversation_id=conv.id)

    properties = Property.objects.filter(status="approved").order_by("name")
    return render(request, "traveler/new_conversation.html", {
        "properties": properties,
    })