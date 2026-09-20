from django import template
from django.db.models import Sum

from accounts.models import ClientUser
from assignments.models import AssignmentLot, TaskDefinition

register = template.Library()


@register.simple_tag
def admin_overview():
    """Small, live operational summary for the admin home page."""
    assignments = AssignmentLot.objects.all()
    completed = assignments.filter(is_completed=True)
    return {
        "employees": ClientUser.objects.count(),
        "demo_users": ClientUser.objects.filter(assignment_status=ClientUser.AssignmentStatus.DEMO).count(),
        "client_users": ClientUser.objects.filter(assignment_status=ClientUser.AssignmentStatus.CLIENT).count(),
        "tasks": TaskDefinition.objects.count(),
        "demo_tasks": TaskDefinition.objects.filter(assignment_type=TaskDefinition.AssignmentType.DEMO).count(),
        "client_tasks": TaskDefinition.objects.filter(assignment_type=TaskDefinition.AssignmentType.CLIENT).count(),
        "assignments": assignments.count(),
        "completed": completed.count(),
        "pending": assignments.filter(is_completed=False).count(),
        "paid_earnings": completed.aggregate(total=Sum("employee_earning"))["total"] or 0,
    }
