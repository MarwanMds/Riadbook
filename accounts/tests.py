from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountsTests(TestCase):

    def test_create_traveler_user(self):
        user = User.objects.create_user(
            email="traveler@test.com",
            password="12345678",
            first_name="Marwan",
            last_name="Merdas",
            role="traveler"
        )

        self.assertEqual(user.email, "traveler@test.com")
        self.assertTrue(user.check_password("12345678"))
        self.assertTrue(user.is_traveler)

    def test_create_owner_user(self):
        user = User.objects.create_user(
            email="owner@test.com",
            password="12345678",
            first_name="Owner",
            last_name="Test",
            role="owner"
        )

        self.assertTrue(user.is_owner)
        self.assertEqual(user.full_name, "Owner Test")