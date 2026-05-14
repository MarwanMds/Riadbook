from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from properties.models import Property
from bookings.models import Booking
from properties.emails import send_property_approved, send_property_rejected
from reviews.models import Review
from messaging.models import Conversation, Message
from messaging.emails import send_new_message_notification


def _admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect("public:home")
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Dashboard ──────────────────────────────────────────────────────────────

@_admin_required
def dashboard_view(request):
    now   = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0)

    stats = {
        "total_users":       User.objects.count(),
        "total_properties":  Property.objects.count(),
        "pending_properties": Property.objects.filter(status="pending").count(),
        "total_bookings":    Booking.objects.count(),
        "bookings_month":    Booking.objects.filter(created_at__gte=month_start).count(),
        "revenue_month":     Booking.objects.filter(
            created_at__gte=month_start,
            status=Booking.Status.CONFIRMED
        ).aggregate(total=Sum("grand_total"))["total"] or 0,
        "pending_reviews":   Review.objects.filter(status="pending").count(),
        "open_conversations": Conversation.objects.filter(
            status="open", unread_by_admin__gt=0
        ).count(),
    }

    recent_bookings = Booking.objects.select_related(
        "traveler", "room__property__city"
    ).order_by("-created_at")[:8]

    pending_properties = Property.objects.filter(
        status="pending"
    ).select_related("owner", "city").order_by("-created_at")[:5]

    pending_reviews = Review.objects.filter(
        status="pending"
    ).select_related("author", "property").order_by("-created_at")[:5]

    return render(request, "backoffice/dashboard.html", {
        "stats":               stats,
        "recent_bookings":     recent_bookings,
        "pending_properties":  pending_properties,
        "pending_reviews":     pending_reviews,
    })


# ── Users ──────────────────────────────────────────────────────────────────

@_admin_required
def users_view(request):
    role   = request.GET.get("role", "")
    search = request.GET.get("q", "").strip()

    users = User.objects.order_by("-date_joined")
    if role:
        users = users.filter(role=role)
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)
        )

    return render(request, "backoffice/users.html", {
        "users":  users,
        "role":   role,
        "search": search,
    })


@_admin_required
def user_toggle_active_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect("backoffice:users")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    action = "activé" if user.is_active else "désactivé"
    messages.success(request, f"Compte de {user.full_name} {action}.")
    return redirect("backoffice:users")


# ── Properties ─────────────────────────────────────────────────────────────

@_admin_required
def properties_view(request):
    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    props = Property.objects.select_related(
        "owner", "city"
    ).order_by("-created_at")

    if status:
        props = props.filter(status=status)
    if search:
        props = props.filter(
            Q(name__icontains=search) |
            Q(owner__email__icontains=search) |
            Q(city__name__icontains=search)
        )

    return render(request, "backoffice/properties.html", {
        "properties":    props,
        "status_filter": status,
        "search":        search,
        "status_choices": Property.Status.choices,
    })


@_admin_required
def property_action_view(request, property_id):
    prop   = get_object_or_404(Property, pk=property_id)
    action = request.POST.get("action")

    if action == "approve":
        prop.status = Property.Status.APPROVED
        prop.save(update_fields=["status"])
        try:
            send_property_approved(prop)
        except Exception:
            pass  # Email failure must never block the admin action
        messages.success(request, f"« {prop.name} » approuvé.")
    elif action == "reject":
        prop.status = Property.Status.REJECTED
        prop.save(update_fields=["status"])
        rejection_reason = request.POST.get("rejection_reason", "").strip()
        try:
            send_property_rejected(prop, reason=rejection_reason)
        except Exception:
            pass
        messages.warning(request, f"« {prop.name} » rejeté.")
    elif action == "suspend":
        prop.status = Property.Status.SUSPENDED
        prop.save(update_fields=["status"])
        messages.warning(request, f"« {prop.name} » suspendu.")
    elif action == "toggle_riad":
        prop.is_authentic_riad = not prop.is_authentic_riad
        prop.save(update_fields=["is_authentic_riad"])
        label = "attribué" if prop.is_authentic_riad else "retiré"
        messages.success(request, f"Label Riad Authentique {label} pour « {prop.name} ».")

    return redirect("backoffice:properties")


# ── Reviews moderation ─────────────────────────────────────────────────────

@_admin_required
def reviews_view(request):
    status = request.GET.get("status", "pending")

    reviews = Review.objects.select_related(
        "author", "property"
    ).order_by("-created_at")

    if status:
        reviews = reviews.filter(status=status)

    return render(request, "backoffice/reviews.html", {
        "reviews":       reviews,
        "status_filter": status,
        "status_choices": Review.Status.choices,
    })


@_admin_required
def review_action_view(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    action = request.POST.get("action")
    note   = request.POST.get("note", "").strip()

    if action == "approve":
        review.status = Review.Status.APPROVED
        review.moderation_note = note
        review.save(update_fields=["status", "moderation_note"])
        _update_property_rating(review.property)
        messages.success(request, "Avis approuvé.")
    elif action == "reject":
        review.status = Review.Status.REJECTED
        review.moderation_note = note
        review.save(update_fields=["status", "moderation_note"])
        messages.warning(request, "Avis rejeté.")

    return redirect("backoffice:reviews")


def _update_property_rating(property):
    agg = Review.objects.filter(
        property=property, status="approved"
    ).aggregate(avg=Avg("rating_overall"), cnt=Count("id"))
    property.avg_rating   = agg["avg"] or 0
    property.review_count = agg["cnt"] or 0
    property.save(update_fields=["avg_rating", "review_count"])


# ── Bookings ───────────────────────────────────────────────────────────────

@_admin_required
def bookings_view(request):
    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()

    bookings = Booking.objects.select_related(
        "traveler", "room__property__city"
    ).order_by("-created_at")

    if status:
        bookings = bookings.filter(status=status)
    if search:
        bookings = bookings.filter(
            Q(reference__icontains=search) |
            Q(guest_email__icontains=search) |
            Q(guest_last_name__icontains=search) |
            Q(room__property__name__icontains=search)
        )

    return render(request, "backoffice/bookings.html", {
        "bookings":      bookings,
        "status_filter": status,
        "search":        search,
        "status_choices": Booking.Status.choices,
    })


# ── Messaging ──────────────────────────────────────────────────────────────

@_admin_required
def messaging_view(request):
    status = request.GET.get("status", "open")
    conversations = Conversation.objects.filter(
        status=status
    ).select_related("traveler", "property").order_by("-last_message_at")

    return render(request, "backoffice/messaging.html", {
        "conversations": conversations,
        "status_filter": status,
    })


@_admin_required
def conversation_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)

    # Mark admin messages as read
    conversation.messages.filter(
        sender_type=Message.SenderType.TRAVELER, is_read=False
    ).update(is_read=True)
    conversation.unread_by_admin = 0
    conversation.save(update_fields=["unread_by_admin"])

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        action = request.POST.get("action", "")

        if body:
            msg = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                sender_type=Message.SenderType.ADMIN,
                body=body,
            )
            conversation.last_message_at    = timezone.now()
            conversation.unread_by_traveler += 1
            conversation.save(update_fields=["last_message_at", "unread_by_traveler"])
            try:
                send_new_message_notification(msg)
            except Exception:
                pass

        if action == "close":
            conversation.status = Conversation.Status.CLOSED
            conversation.save(update_fields=["status"])
            messages.success(request, "Conversation fermée.")
            return redirect("backoffice:messaging")

        return redirect("backoffice:conversation", conversation_id=conversation_id)

    msgs = conversation.messages.select_related("sender").order_by("created_at")
    return render(request, "backoffice/conversation.html", {
        "conversation": conversation,
        "messages":     msgs,
    })


# ── Stats ──────────────────────────────────────────────────────────────────

@_admin_required
def stats_view(request):
    from django.db.models.functions import TruncMonth

    bookings_by_month = (
        Booking.objects
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"), revenue=Sum("grand_total"))
        .order_by("month")
    )

    top_cities = (
        Booking.objects
        .values("room__property__city__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:6]
    )

    top_properties = (
        Booking.objects
        .values("room__property__name")
        .annotate(count=Count("id"), revenue=Sum("grand_total"))
        .order_by("-count")[:8]
    )

    users_by_role = User.objects.values("role").annotate(count=Count("id"))

    return render(request, "backoffice/stats.html", {
        "bookings_by_month": list(bookings_by_month),
        "top_cities":        list(top_cities),
        "top_properties":    list(top_properties),
        "users_by_role":     list(users_by_role),
    })
