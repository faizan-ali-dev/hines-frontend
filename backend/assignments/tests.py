from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AssignmentLot, ProgressChange
from .services import (
    CLIENT_TOTAL_LOTS,
    DEMO_TOTAL_LOTS,
    activate_client_account,
    assignment_summary,
    create_default_lots,
    set_progress,
)


class AssignmentServiceTests(TestCase):
    def setUp(self):
        self.employee = get_user_model().objects.create_user(
            username="john@example.com",
            email="john@example.com",
            password="A-strong-password-2026",
            first_name="John",
            last_name="Smith",
        )
        create_default_lots(self.employee)

    def test_default_lots_match_required_assignment_sizes(self):
        self.assertEqual(
            AssignmentLot.objects.filter(assignment_type=AssignmentLot.AssignmentType.DEMO).count(),
            DEMO_TOTAL_LOTS,
        )
        self.assertEqual(
            AssignmentLot.objects.filter(assignment_type=AssignmentLot.AssignmentType.CLIENT).count(),
            CLIENT_TOTAL_LOTS,
        )

    def test_progress_marks_only_the_first_lots_and_recalculates_earnings(self):
        set_progress(self.employee, AssignmentLot.AssignmentType.DEMO, 6)

        summary = assignment_summary(self.employee, AssignmentLot.AssignmentType.DEMO)
        self.assertEqual(summary["completed"], 6)
        self.assertEqual(summary["remaining"], 9)
        self.assertEqual(summary["current_earnings"], Decimal("31.00"))
        self.assertEqual(summary["percentage"], 40.0)
        self.assertTrue(AssignmentLot.objects.get(assignment_type="demo", lot_number=6).is_completed)
        self.assertFalse(AssignmentLot.objects.get(assignment_type="demo", lot_number=7).is_completed)

        set_progress(self.employee, AssignmentLot.AssignmentType.DEMO, 5)
        self.assertFalse(AssignmentLot.objects.get(assignment_type="demo", lot_number=6).is_completed)
        self.assertEqual(
            assignment_summary(self.employee, AssignmentLot.AssignmentType.DEMO)["current_earnings"],
            Decimal("25.00"),
        )
        self.assertEqual(ProgressChange.objects.count(), 2)

    def test_client_activation_carries_demo_earnings_once(self):
        with self.assertRaisesMessage(ValueError, "Demo progress must be 15"):
            activate_client_account(self.employee)

        set_progress(self.employee, AssignmentLot.AssignmentType.DEMO, 15)
        activated = activate_client_account(self.employee)
        self.assertTrue(activated.client_is_active)
        self.assertEqual(activated.carried_demo_earnings, Decimal("65.00"))

        set_progress(self.employee, AssignmentLot.AssignmentType.DEMO, 14)
        activated_again = activate_client_account(self.employee)
        self.assertEqual(activated_again.carried_demo_earnings, Decimal("65.00"))

# Create your tests here.
