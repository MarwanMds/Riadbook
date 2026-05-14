from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages

from .models import Conversation, Message


@login_required
def inbox_view(request):
    """Redirect to correct messaging dashboard based on role."""
    if request.user.is_traveler:
        return redirect("traveler:messaging")
    elif request.user.is_owner:
        return redirect("owner:dashboard")
    elif request.user.is_admin:
        return redirect("backoffice:messaging")
    return redirect("public:home")