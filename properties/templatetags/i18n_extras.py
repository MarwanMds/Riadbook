"""
Custom template tags for multilingual field display.
Usage:
  {% load i18n_extras %}
  {{ city|translated_name }}
  {{ amenity|translated_name }}
"""
from django import template
from django.utils.translation import get_language

register = template.Library()


@register.filter
def translated_name(obj):
    """
    Returns the translated name of a City or Amenity based on the active language.
    Falls back to the default French name if translation is missing.
    """
    lang = get_language()  # e.g. 'ar', 'en', 'fr'

    if lang == 'ar' and hasattr(obj, 'name_ar') and obj.name_ar:
        return obj.name_ar
    if lang == 'en' and hasattr(obj, 'name_en') and obj.name_en:
        return obj.name_en
    return obj.name


@register.filter
def status_label(booking):
    """Returns translated booking status label."""
    from django.utils.translation import gettext as _
    labels = {
        'pending':   _('booking.status_pending'),
        'confirmed': _('booking.status_confirmed'),
        'cancelled': _('booking.status_cancelled'),
        'completed': _('booking.status_completed'),
    }
    return labels.get(booking.status, booking.status)


@register.filter
def conv_status_label(status):
    """Returns translated conversation status."""
    from django.utils.translation import gettext as _
    labels = {
        'open':    _('Ouvert'),
        'closed':  _('Fermé'),
        'pending': _('En attente'),
    }
    return labels.get(status, status)
