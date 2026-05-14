from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """Generic decorator — usage: @role_required('owner') or @role_required('admin')"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/accounts/login/?next={request.path}")
            if request.user.role not in roles:
                messages.error(request, "Accès refusé.")
                return redirect("/")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Convenience aliases
traveler_required = role_required("traveler")
owner_required    = role_required("owner")
admin_required    = role_required("admin")
owner_or_admin    = role_required("owner", "admin")
