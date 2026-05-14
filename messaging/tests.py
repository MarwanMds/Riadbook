from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Conversation, Message, Notification

User = get_user_model()


class MessagingTests(TestCase):

    def setUp(self):
        self.traveler = User.objects.create_user(
            email="traveler@test.com",
            password="12345678",
            first_name="Marwan",
            last_name="Merdas",
            role="traveler"
        )

    def test_create_conversation(self):
        conversation = Conversation.objects.create(
            traveler=self.traveler,
            subject="Question sur une réservation"
        )

        self.assertEqual(conversation.subject, "Question sur une réservation")
        self.assertEqual(conversation.status, "open")

    def test_create_message(self):
        conversation = Conversation.objects.create(
            traveler=self.traveler,
            subject="Demande d'information"
        )

        message = Message.objects.create(
            conversation=conversation,
            sender=self.traveler,
            sender_type="traveler",
            body="Bonjour, est-ce que la chambre est disponible ?"
        )

        self.assertEqual(message.body, "Bonjour, est-ce que la chambre est disponible ?")
        self.assertFalse(message.is_read)

    def test_create_notification(self):
        notification = Notification.objects.create(
            user=self.traveler,
            notif_type="new_message",
            title="Nouveau message",
            body="Vous avez reçu un nouveau message."
        )

        self.assertEqual(notification.title, "Nouveau message")
        self.assertFalse(notification.is_read)