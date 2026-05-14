from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import City, Property, Room

User = get_user_model()


class PropertiesTests(TestCase):

    def setUp(self):
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
            description="Un beau riad traditionnel.",
            property_type="riad",
            city=self.city,
            address="Marrakech Medina",
            status="approved"
        )

    def test_create_property(self):
        self.assertEqual(self.property.name, "Riad Atlas")
        self.assertEqual(self.property.city.name, "Marrakech")
        self.assertEqual(str(self.property), "Riad Atlas")

    def test_create_room(self):
        room = Room.objects.create(
            property=self.property,
            name="Suite Deluxe",
            capacity=2,
            price_per_night=500
        )

        self.assertEqual(room.property.name, "Riad Atlas")
        self.assertEqual(room.price_per_night, 500)