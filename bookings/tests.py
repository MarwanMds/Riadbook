from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from properties.models import City, Property, Room
from .models import Booking, Availability, Favorite

User = get_user_model()


class BookingsTests(TestCase):

    def setUp(self):
        self.traveler = User.objects.create_user(
            email="traveler@test.com",
            password="12345678",
            first_name="Marwan",
            last_name="Merdas",
            role="traveler"
        )

        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="12345678",
            first_name="Owner",
            last_name="Test",
            role="owner"
        )

        self.city = City.objects.create(
            name="Marrakech",
            slug="marrakech",
            latitude=31.629500,
            longitude=-7.981100
        )

        self.property = Property.objects.create(
            owner=self.owner,
            name="Riad Atlas",
            slug="riad-atlas",
            description="Un beau riad.",
            property_type="riad",
            city=self.city,
            address="Marrakech",
            status="approved"
        )

        self.room = Room.objects.create(
            property=self.property,
            name="Chambre Double",
            capacity=2,
            price_per_night=400
        )

    def test_create_booking(self):
        booking = Booking.objects.create(
            traveler=self.traveler,
            room=self.room,
            check_in=date(2026, 6, 1),
            check_out=date(2026, 6, 3),
            price_per_night=400,
            total_price=800,
            taxes=0,
            grand_total=800,
            guest_first_name="Marwan",
            guest_last_name="Merdas",
            guest_email="traveler@test.com"
        )

        self.assertEqual(booking.num_nights, 2)
        self.assertTrue(booking.reference.startswith("RB"))

    def test_create_availability(self):
        availability = Availability.objects.create(
            room=self.room,
            date=date(2026, 6, 1),
            is_available=False,
            note="Booked"
        )

        self.assertFalse(availability.is_available)

    def test_add_favorite(self):
        favorite = Favorite.objects.create(
            traveler=self.traveler,
            property=self.property
        )

        self.assertEqual(favorite.property.name, "Riad Atlas")