from django.test import TestCase
from django.urls import reverse

from assignments.models import AssignmentLot
from assignments.services import activate_client_account, set_progress

from .models import ClientUser


class ClientPageTests(TestCase):
    signup_payload = {
        "full_name": "Faizan Ali",
        "email": "faizan@example.com",
        "referral_code": "HINES-2026",
        "password": "A-strong-password-2026",
    }

    def test_signup_creates_an_authenticated_client_and_demo_dashboard(self):
        response = self.client.post(reverse("accounts:signup"), self.signup_payload)

        self.assertRedirects(response, reverse("accounts:demo-dashboard"))
        self.assertEqual(ClientUser.objects.count(), 1)
        self.assertEqual(AssignmentLot.objects.filter(employee__email="faizan@example.com").count(), 50)
        dashboard_response = self.client.get(reverse("accounts:demo-dashboard"))
        self.assertContains(dashboard_response, "Demo Assignment")
        self.assertContains(dashboard_response, "#001")
        self.assertContains(dashboard_response, "$0.00")

    def test_client_dashboard_stays_locked_until_staff_activation(self):
        self.client.post(reverse("accounts:signup"), self.signup_payload)
        employee = ClientUser.objects.get(email="faizan@example.com")
        self.assertEqual(self.client.get(reverse("accounts:client-dashboard")).status_code, 403)

        set_progress(employee, AssignmentLot.AssignmentType.DEMO, 15)
        activate_client_account(employee)

        response = self.client.get(reverse("accounts:client-dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo Earnings Carried Forward")
        self.assertContains(response, "$65.00")

    def test_client_can_log_in_and_log_out_with_browser_forms(self):
        self.client.post(reverse("accounts:signup"), self.signup_payload)
        self.client.post(reverse("accounts:logout"))

        login_response = self.client.post(
            reverse("accounts:login"),
            {"username": "faizan@example.com", "password": self.signup_payload["password"]},
        )
        self.assertRedirects(login_response, reverse("accounts:demo-dashboard"))
        self.assertContains(self.client.get(reverse("accounts:demo-dashboard")), "Faizan")

        logout_response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(logout_response, reverse("accounts:login"))
        self.assertEqual(self.client.get(reverse("accounts:demo-dashboard")).status_code, 302)

    def test_signup_rejects_duplicate_emails(self):
        self.client.post(reverse("accounts:signup"), self.signup_payload)
        self.client.post(reverse("accounts:logout"))

        response = self.client.post(reverse("accounts:signup"), self.signup_payload)
        self.assertContains(response, "An account with this email already exists.")

    def test_public_frontend_pages_use_the_server_auth_routes(self):
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        home_content = b"".join(home.streaming_content).decode("utf-8")
        self.assertIn('href="/sign-up/"', home_content)
        self.assertIn('href="/client-login/"', home_content)
        self.assertEqual(self.client.get("/investment-management/").status_code, 200)

    def test_admin_control_table_exposes_progress_and_earnings_columns(self):
        admin_user = ClientUser.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="A-strong-password-2026",
        )
        self.client.force_login(admin_user)

        response = self.client.get("/admin/accounts/clientuser/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo earnings")
        self.assertContains(response, "Client earnings")
        self.assertContains(response, "Total earnings")
