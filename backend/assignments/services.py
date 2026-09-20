from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import AssignmentLot, ProgressChange

DEMO_TOTAL_LOTS = 15
CLIENT_TOTAL_LOTS = 35
DEMO_TASK_VALUES = (60, 45, 50, 55, 40, 60, 50, 40, 35, 45, 50, 30, 40, 25, 25)
CLIENT_TASK_VALUES = (250, 275, 200, 300, 225) * 6 + (250, 275, 200, 300, 475)


def total_lots(assignment_type):
    if assignment_type == AssignmentLot.AssignmentType.DEMO:
        return DEMO_TOTAL_LOTS
    if assignment_type == AssignmentLot.AssignmentType.CLIENT:
        return CLIENT_TOTAL_LOTS
    raise ValueError("Unknown assignment type.")


def _task_values(assignment_type):
    if assignment_type == AssignmentLot.AssignmentType.DEMO:
        return DEMO_TASK_VALUES
    if assignment_type == AssignmentLot.AssignmentType.CLIENT:
        return CLIENT_TASK_VALUES
    raise ValueError("Unknown assignment type.")


def create_default_lots(employee):
    """Creates the employee's 15 demo and 35 client lots exactly once."""
    lots = []
    for assignment_type in AssignmentLot.AssignmentType.values:
        for number, value in enumerate(_task_values(assignment_type), start=1):
            task_value = Decimal(str(value)).quantize(Decimal("0.01"))
            lots.append(
                AssignmentLot(
                    employee=employee,
                    assignment_type=assignment_type,
                    lot_number=number,
                    task_name="Property Task" if assignment_type == "demo" else "Client Task",
                    task_description="Complete the assigned property review task.",
                    task_value=task_value,
                    employee_earning=(task_value * Decimal("0.10")).quantize(Decimal("0.01")),
                    task_link="https://www.hines.com/",
                )
            )
    AssignmentLot.objects.bulk_create(lots, ignore_conflicts=True)


def assignment_summary(employee, assignment_type):
    lots = list(employee.assignment_lots.filter(assignment_type=assignment_type).order_by("lot_number"))
    expected_total = total_lots(assignment_type)
    if len(lots) != expected_total:
        create_default_lots(employee)
        lots = list(employee.assignment_lots.filter(assignment_type=assignment_type).order_by("lot_number"))

    completed_lots = [lot for lot in lots if lot.is_completed]
    current_earnings = sum((lot.employee_earning for lot in completed_lots), Decimal("0.00"))
    potential_earnings = sum((lot.employee_earning for lot in lots), Decimal("0.00"))
    completed = len(completed_lots)
    return {
        "lots": lots,
        "total_lots": len(lots),
        "completed": completed,
        "remaining": len(lots) - completed,
        "percentage": round((completed / len(lots)) * 100, 2) if lots else 0,
        "current_earnings": current_earnings,
        "potential_earnings": potential_earnings,
        "remaining_potential": potential_earnings - current_earnings,
    }


@transaction.atomic
def set_progress(employee, assignment_type, progress, changed_by=None, previous_progress=None):
    expected_total = total_lots(assignment_type)
    if not isinstance(progress, int) or isinstance(progress, bool) or not 0 <= progress <= expected_total:
        raise ValueError(f"Progress must be a whole number from 0 to {expected_total}.")

    employee = type(employee).objects.select_for_update().get(pk=employee.pk)
    create_default_lots(employee)
    progress_field = "demo_progress" if assignment_type == AssignmentLot.AssignmentType.DEMO else "client_progress"
    stored_progress = getattr(employee, progress_field)
    previous_progress = stored_progress if previous_progress is None else previous_progress

    lots = AssignmentLot.objects.select_for_update().filter(employee=employee, assignment_type=assignment_type)
    lots.filter(lot_number__lte=progress).update(is_completed=True)
    lots.filter(lot_number__gt=progress).update(is_completed=False)
    if stored_progress != progress:
        setattr(employee, progress_field, progress)
        employee.save(update_fields=(progress_field,))
    if previous_progress != progress:
        ProgressChange.objects.create(
            employee=employee,
            assignment_type=assignment_type,
            previous_progress=previous_progress,
            new_progress=progress,
            changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
        )
    return employee


@transaction.atomic
def activate_client_account(employee, changed_by=None):
    employee = type(employee).objects.select_for_update().get(pk=employee.pk)
    if employee.client_activated_at is not None:
        return employee
    demo = assignment_summary(employee, AssignmentLot.AssignmentType.DEMO)
    if demo["completed"] != DEMO_TOTAL_LOTS:
        raise ValueError("Demo progress must be 15 before the client account can be activated.")
    employee.carried_demo_earnings = demo["current_earnings"]
    employee.client_activated_at = timezone.now()
    employee.save(update_fields=("carried_demo_earnings", "client_activated_at"))
    return employee
