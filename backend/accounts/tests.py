import json

from django.test import TestCase
from django.urls import reverse

from .models import ClientUser


class AuthenticationApiTests(TestCase):
    signup_payload = {
        "full_name": "Faizan Ali",
        "email": "faizan@example.com",
        "referral_code": "HINES-2026",
        "password": "A-strong-password-2026",
    }

    def post_json(self, url, payload):
        return self.client.post(url, data=json.dumps(payload), content_type="application/json")

    def test_signup_creates_and_authenticates_a_client(self):
        response = self.post_json(reverse("accounts:signup"), self.signup_payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ClientUser.objects.count(), 1)
        self.assertEqual(response.json()["user"]["full_name"], "Faizan Ali")
        self.assertEqual(response.json()["user"]["referral_code"], "HINES-2026")
        self.assertEqual(self.client.get(reverse("accounts:dashboard")).status_code, 200)

    def test_client_can_log_in_with_signup_email_and_log_out(self):
        self.post_json(reverse("accounts:signup"), self.signup_payload)
        self.post_json(reverse("accounts:logout"), {})

        login_response = self.post_json(
            reverse("accounts:login"),
            {"username": "faizan@example.com", "password": self.signup_payload["password"]},
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:profile")).json()["user"]["email"], "faizan@example.com")

        logout_response = self.post_json(reverse("accounts:logout"), {})
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:dashboard")).status_code, 401)

    def test_signup_rejects_duplicate_emails(self):
        self.post_json(reverse("accounts:signup"), self.signup_payload)

        response = self.post_json(reverse("accounts:signup"), self.signup_payload)
        self.assertEqual(response.status_code, 409)

# Create your tests here.
