from decimal import Decimal

from django.contrib import admin

from .models import AssignmentLot, ProgressChange


@admin.register(AssignmentLot)
class AssignmentLotAdmin(admin.ModelAdmin):
    list_display = ("employee", "assignment_type", "lot_number", "task_name", "task_value", "employee_earning", "is_completed")
    list_filter = ("assignment_type", "is_completed")
    search_fields = ("employee__email", "employee__first_name", "employee__last_name", "task_name")
    ordering = ("employee__email", "assignment_type", "lot_number")
    readonly_fields = ("is_completed",)

    def save_model(self, request, obj, form, change):
        if obj.assignment_type == AssignmentLot.AssignmentType.DEMO:
            obj.employee_earning = (obj.task_value * Decimal("0.10")).quantize(Decimal("0.01"))
        super().save_model(request, obj, form, change)


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
