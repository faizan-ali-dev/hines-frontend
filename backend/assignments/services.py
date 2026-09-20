from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import AssignmentLot, ProgressChange, TaskDefinition

DEMO_TOTAL_LOTS = 15
CLIENT_TOTAL_LOTS = 35
DEMO_TASK_VALUES = (60, 45, 50, 55, 40, 60, 50, 40, 35, 45, 50, 30, 40, 25, 25)
CLIENT_TASK_VALUES = (250, 275, 200, 300, 225) * 6 + (250, 275, 200, 300, 475)


def _task_values(assignment_type):
    if assignment_type == TaskDefinition.AssignmentType.DEMO:
        return DEMO_TASK_VALUES
    if assignment_type == TaskDefinition.AssignmentType.CLIENT:
        return CLIENT_TASK_VALUES
    raise ValueError("Unknown assignment type.")


@transaction.atomic
def ensure_default_task_definitions():
    """Seed the standard catalogue once, so all users share the same tasks."""
    for assignment_type in TaskDefinition.AssignmentType.values:
        if TaskDefinition.objects.filter(assignment_type=assignment_type).exists():
            continue
        definitions = []
        for number, value in enumerate(_task_values(assignment_type), start=1):
            task_value = Decimal(str(value)).quantize(Decimal("0.01"))
            definitions.append(TaskDefinition(
                assignment_type=assignment_type,
                lot_number=number,
                task_name="Property Task" if assignment_type == TaskDefinition.AssignmentType.DEMO else "Client Task",
                task_description="Complete the assigned property review task.",
                task_value=task_value,
                employee_earning=(task_value * Decimal("0.10")).quantize(Decimal("0.01")),
                task_link="https://www.hines.com/",
            ))
        TaskDefinition.objects.bulk_create(definitions, ignore_conflicts=True)


def _assignment_for(employee, task):
    return AssignmentLot(
        employee=employee, task_definition=task, assignment_type=task.assignment_type,
        lot_number=task.lot_number, task_name=task.task_name,
        task_description=task.task_description, task_value=task.task_value,
        employee_earning=task.employee_earning, task_link=task.task_link,
    )


@transaction.atomic
def ensure_assignments(employee, assignment_type):
    """Give an eligible employee every task in the shared catalogue."""
    ensure_default_task_definitions()
    if assignment_type == TaskDefinition.AssignmentType.CLIENT and not employee.client_is_active:
        return
    if assignment_type == TaskDefinition.AssignmentType.DEMO and employee.client_is_active:
        return
    definitions = list(TaskDefinition.objects.filter(assignment_type=assignment_type).order_by("lot_number"))
    existing_ids = set(AssignmentLot.objects.filter(employee=employee, task_definition__in=definitions).values_list("task_definition_id", flat=True))
    AssignmentLot.objects.bulk_create(
        [_assignment_for(employee, task) for task in definitions if task.pk not in existing_ids], ignore_conflicts=True,
    )


@transaction.atomic
def assign_task_to_eligible_users(task):
    """Assign an administrator-created catalogue task to every user in its stage."""
    from accounts.models import ClientUser

    users = ClientUser.objects.filter(assignment_status=task.assignment_type)
    existing_user_ids = set(AssignmentLot.objects.filter(task_definition=task).values_list("employee_id", flat=True))
    assignments = [_assignment_for(employee, task) for employee in users if employee.pk not in existing_user_ids]
    AssignmentLot.objects.bulk_create(assignments, ignore_conflicts=True)
    return len(assignments)


def create_default_lots(employee):
    """Compatibility entry point used after creating an employee."""
    ensure_assignments(employee, TaskDefinition.AssignmentType.DEMO)
    if employee.client_is_active:
        ensure_assignments(employee, TaskDefinition.AssignmentType.CLIENT)


def assignment_summary(employee, assignment_type):
    ensure_assignments(employee, assignment_type)
    lots = list(employee.assignment_lots.filter(assignment_type=assignment_type).order_by("lot_number"))
    completed_lots = [lot for lot in lots if lot.is_completed]
    current_earnings = sum((lot.employee_earning for lot in completed_lots), Decimal("0.00"))
    potential_earnings = sum((lot.employee_earning for lot in lots), Decimal("0.00"))
    completed = len(completed_lots)
    return {
        "lots": lots, "total_lots": len(lots), "completed": completed,
        "remaining": len(lots) - completed,
        "percentage": round((completed / len(lots)) * 100, 2) if lots else 0,
        "current_earnings": current_earnings, "potential_earnings": potential_earnings,
        "remaining_potential": potential_earnings - current_earnings,
    }


@transaction.atomic
def sync_progress_from_lots(employee, assignment_type, changed_by=None):
    employee = type(employee).objects.select_for_update().get(pk=employee.pk)
    progress_field = "demo_progress" if assignment_type == TaskDefinition.AssignmentType.DEMO else "client_progress"
    previous_progress = getattr(employee, progress_field)
    completed = AssignmentLot.objects.filter(employee=employee, assignment_type=assignment_type, is_completed=True).count()
    if previous_progress != completed:
        setattr(employee, progress_field, completed)
        employee.save(update_fields=(progress_field,))
        ProgressChange.objects.create(
            employee=employee, assignment_type=assignment_type, previous_progress=previous_progress,
            new_progress=completed, changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
        )
    return employee


@transaction.atomic
def set_progress(employee, assignment_type, progress, changed_by=None, previous_progress=None):
    employee = type(employee).objects.select_for_update().get(pk=employee.pk)
    ensure_assignments(employee, assignment_type)
    lots = list(AssignmentLot.objects.select_for_update().filter(employee=employee, assignment_type=assignment_type).order_by("lot_number"))
    expected_total = len(lots)
    if not isinstance(progress, int) or isinstance(progress, bool) or not 0 <= progress <= expected_total:
        raise ValueError(f"Progress must be a whole number from 0 to {expected_total}.")
    progress_field = "demo_progress" if assignment_type == TaskDefinition.AssignmentType.DEMO else "client_progress"
    stored_progress = getattr(employee, progress_field)
    previous_progress = stored_progress if previous_progress is None else previous_progress
    completed_ids = [lot.pk for lot in lots[:progress]]
    AssignmentLot.objects.filter(pk__in=completed_ids).update(is_completed=True)
    AssignmentLot.objects.filter(employee=employee, assignment_type=assignment_type).exclude(pk__in=completed_ids).update(is_completed=False)
    if stored_progress != progress:
        setattr(employee, progress_field, progress)
        employee.save(update_fields=(progress_field,))
    if previous_progress != progress:
        ProgressChange.objects.create(
            employee=employee, assignment_type=assignment_type, previous_progress=previous_progress,
            new_progress=progress, changed_by=changed_by if getattr(changed_by, "is_authenticated", False) else None,
        )
    return employee


@transaction.atomic
def activate_client_account(employee, changed_by=None, require_completed=True):
    employee = type(employee).objects.select_for_update().get(pk=employee.pk)
    if employee.client_activated_at is not None:
        if employee.assignment_status != employee.AssignmentStatus.CLIENT:
            employee.assignment_status = employee.AssignmentStatus.CLIENT
            employee.save(update_fields=("assignment_status",))
        ensure_assignments(employee, TaskDefinition.AssignmentType.CLIENT)
        return employee
    demo = assignment_summary(employee, TaskDefinition.AssignmentType.DEMO)
    if require_completed and demo["completed"] != demo["total_lots"]:
        raise ValueError("All Demo lots must be completed before the client account can be activated.")
    update_fields = []
    if employee.client_activated_at is None:
        employee.carried_demo_earnings = demo["current_earnings"]
        employee.client_activated_at = timezone.now()
        update_fields.extend(("carried_demo_earnings", "client_activated_at"))
    if employee.assignment_status != employee.AssignmentStatus.CLIENT:
        employee.assignment_status = employee.AssignmentStatus.CLIENT
        update_fields.append("assignment_status")
    if update_fields:
        employee.save(update_fields=update_fields)
    ensure_assignments(employee, TaskDefinition.AssignmentType.CLIENT)
    return employee


@transaction.atomic
def set_assignment_status(employee, status, changed_by=None):
    if status == employee.AssignmentStatus.CLIENT:
        return activate_client_account(employee, changed_by=changed_by, require_completed=False)
    if status != employee.AssignmentStatus.DEMO:
        raise ValueError("Unknown assignment status.")
    employee = type(employee).objects.select_for_update().get(pk=employee.pk)
    if employee.assignment_status != employee.AssignmentStatus.DEMO:
        employee.assignment_status = employee.AssignmentStatus.DEMO
        employee.save(update_fields=("assignment_status",))
    AssignmentLot.objects.filter(employee=employee, assignment_type=TaskDefinition.AssignmentType.CLIENT).delete()
    ensure_assignments(employee, TaskDefinition.AssignmentType.DEMO)
    return employee
