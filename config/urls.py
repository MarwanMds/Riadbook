from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language

urlpatterns = [
    path("django-admin/",    admin.site.urls),
    path("accounts/",        include("accounts.urls",   namespace="accounts")),
    path("",                 include("public.urls",     namespace="public")),
    path("",                 include("properties.urls", namespace="properties")),
    path("",                 include("reviews.urls",    namespace="reviews")),
    path("",                 include("bookings.urls",   namespace="bookings")),
    path("dashboard/",       include("traveler.urls",   namespace="traveler")),
    path("owner/",           include("owner.urls",      namespace="owner")),
    path("admin-dashboard/", include("backoffice.urls", namespace="backoffice")),
    path("i18n/",            include("django.conf.urls.i18n")),
    path("i18n/set_language/", set_language, name="set_language"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)