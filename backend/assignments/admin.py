from django.contrib import admin

from .models import AssignmentLot, ProgressChange, TaskDefinition
from .services import assign_task_to_eligible_users, sync_progress_from_lots


@admin.register(TaskDefinition)
class TaskDefinitionAdmin(admin.ModelAdmin):
    """The shared task catalogue. One task is distributed to every eligible user."""

    list_display = ("assignment_type", "lot_number", "task_name", "task_value", "employee_earning", "task_link", "assigned_users")
    list_filter = ("assignment_type",)
    search_fields = ("task_name", "task_description")
    ordering = ("assignment_type", "lot_number")

    def get_readonly_fields(self, request, obj=None):
        return ("assignment_type", "lot_number") if obj else ()

    @admin.display(description="Assigned users")
    def assigned_users(self, obj):
        return obj.assignments.count()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            assign_task_to_eligible_users(obj)
            return
        obj.assignments.update(
            assignment_type=obj.assignment_type, lot_number=obj.lot_number, task_name=obj.task_name,
            task_description=obj.task_description, task_value=obj.task_value,
            employee_earning=obj.employee_earning, task_link=obj.task_link,
        )

    def delete_model(self, request, obj):
        affected = list(obj.assignments.values_list("employee_id", flat=True))
        assignment_type = obj.assignment_type
        super().delete_model(request, obj)
        from accounts.models import ClientUser
        for employee_id in affected:
            sync_progress_from_lots(ClientUser.objects.get(pk=employee_id), assignment_type, changed_by=request.user)

    def delete_queryset(self, request, queryset):
        affected = [
            (task.assignment_type, list(task.assignments.values_list("employee_id", flat=True)))
            for task in queryset
        ]
        queryset.delete()
        from accounts.models import ClientUser
        for assignment_type, employee_ids in affected:
            for employee_id in employee_ids:
                sync_progress_from_lots(ClientUser.objects.get(pk=employee_id), assignment_type, changed_by=request.user)


@admin.register(AssignmentLot)
class AssignmentLotAdmin(admin.ModelAdmin):
    """Staff manage each employee's completion status here."""

    list_display = ("employee", "assignment_type", "lot_number", "task_name", "task_value", "employee_earning", "task_link", "is_completed")
    list_editable = ("is_completed",)
    list_filter = ("assignment_type", "is_completed")
    search_fields = ("employee__email", "employee__first_name", "employee__last_name", "task_name")
    ordering = ("employee__email", "assignment_type", "lot_number")
    readonly_fields = ("employee", "task_definition", "assignment_type", "lot_number", "task_name", "task_description", "task_value", "employee_earning", "task_link")
    fields = readonly_fields + ("is_completed",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        sync_progress_from_lots(obj.employee, obj.assignment_type, changed_by=request.user)


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
