from django.contrib import admin
from .models import City, Amenity, Property, PropertyPhoto, Room, RoomPhoto


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "name_en", "icon")


class PropertyPhotoInline(admin.TabularInline):
    model = PropertyPhoto
    extra = 1


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1
    fields = ("name", "bed_type", "capacity", "price_per_night", "is_active")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display   = ("name", "owner", "city", "property_type", "status", "avg_rating", "review_count")
    list_filter    = ("status", "property_type", "city", "is_authentic_riad")
    search_fields  = ("name", "owner__email", "city__name")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal  = ("amenities",)
    inlines        = [PropertyPhotoInline, RoomInline]
    readonly_fields = ("avg_rating", "review_count", "created_at", "updated_at")
    actions        = ["approve_properties", "reject_properties"]

    def approve_properties(self, request, queryset):
        queryset.update(status="approved")
    approve_properties.short_description = "Approuver les établissements sélectionnés"

    def reject_properties(self, request, queryset):
        queryset.update(status="rejected")
    reject_properties.short_description = "Rejeter les établissements sélectionnés"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "property", "bed_type", "capacity", "price_per_night", "is_active")
    list_filter  = ("bed_type", "is_active", "free_cancellation")
