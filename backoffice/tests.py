from django.test import TestCase
from django.urls import reverse


class BackofficeTests(TestCase):

    def test_backoffice_url_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('backoffice:dashboard'))

        self.assertEqual(response.status_code, 302)