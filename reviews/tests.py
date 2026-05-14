from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date
from properties.models import City, Property, Room
from bookings.models import Booking
from .models import Review, OwnerReply

User = get_user_model()


class ReviewsTests(TestCase):

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

        self.booking = Booking.objects.create(
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
            guest_email="traveler@test.com",
            status="completed"
        )

    def test_create_verified_review(self):
        review = Review.objects.create(
            property=self.property,
            author=self.traveler,
            booking=self.booking,
            rating_overall=5,
            comment="Excellent séjour."
        )

        self.assertTrue(review.is_verified)
        self.assertEqual(review.rating_overall, 5)

    def test_owner_reply_to_review(self):
        review = Review.objects.create(
            property=self.property,
            author=self.traveler,
            rating_overall=4,
            comment="Très bon riad."
        )

        reply = OwnerReply.objects.create(
            review=review,
            author=self.owner,
            comment="Merci pour votre avis."
        )

        self.assertEqual(reply.review, review)
        self.assertEqual(reply.author, self.owner)