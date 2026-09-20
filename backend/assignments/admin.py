from django.contrib import admin

from .models import AssignmentLot, ProgressChange
from .services import sync_progress_from_lots


@admin.register(AssignmentLot)
class AssignmentLotAdmin(admin.ModelAdmin):
    """Staff can create and edit every task detail, link, earning, and status."""

    list_display = ("employee", "assignment_type", "lot_number", "task_name", "task_value", "employee_earning", "task_link", "is_completed")
    list_filter = ("assignment_type", "is_completed")
    search_fields = ("employee__email", "employee__first_name", "employee__last_name", "task_name")
    ordering = ("employee__email", "assignment_type", "lot_number")

    def save_model(self, request, obj, form, change):
        previous = AssignmentLot.objects.get(pk=obj.pk) if change else None
        super().save_model(request, obj, form, change)
        sync_progress_from_lots(obj.employee, obj.assignment_type, changed_by=request.user)
        if previous and (previous.employee_id != obj.employee_id or previous.assignment_type != obj.assignment_type):
            sync_progress_from_lots(previous.employee, previous.assignment_type, changed_by=request.user)

    def delete_model(self, request, obj):
        employee = obj.employee
        assignment_type = obj.assignment_type
        super().delete_model(request, obj)
        sync_progress_from_lots(employee, assignment_type, changed_by=request.user)


@admin.register(ProgressChange)
class ProgressChangeAdmin(admin.ModelAdmin):
    list_display = ("employee", "assignment_type", "previous_progress", "new_progress", "changed_by", "created_at")
    list_filter = ("assignment_type", "created_at")
    search_fields = ("employee__email", "changed_by__email")
    readonly_fields = ("employee", "assignment_type", "previous_progress", "new_progress", "changed_by", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
