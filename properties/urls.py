from django.urls import path
from . import views

app_name = "properties"

urlpatterns = [
    path("search/",         views.search_view,       name="search"),
    path("riads/",          views.riad_showcase_view, name="riads"),
    path("property/<slug:slug>/", views.property_detail_view, name="detail"),
]