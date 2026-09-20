from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from assignments.models import AssignmentLot
from assignments.services import (
    activate_client_account,
    assignment_summary,
    create_default_lots,
    set_assignment_status,
    set_progress,
)
from .models import ClientUser


admin.site.site_header = "Hines Assignment Control Panel"
admin.site.site_title = "Hines Control Panel"
admin.site.index_title = "Employee assignments"


class AssignmentStatusFilter(admin.SimpleListFilter):
    title = "assignment status"
    parameter_name = "assignment_status"

    def lookups(self, request, model_admin):
        return (
            ("demo-active", "Demo active"),
            ("demo-completed", "Demo completed"),
            ("client-active", "Client active"),
            ("assignment-completed", "Assignment completed"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "demo-active":
            return queryset.filter(assignment_status=ClientUser.AssignmentStatus.DEMO)
        if value == "demo-completed":
            return queryset.filter(client_activated_at__isnull=False)
        if value == "client-active":
            return queryset.filter(assignment_status=ClientUser.AssignmentStatus.CLIENT)
        if value == "assignment-completed":
            return queryset.filter(assignment_status=ClientUser.AssignmentStatus.CLIENT, client_progress__gt=0)
        return queryset


@admin.register(ClientUser)
class ClientUserAdmin(UserAdmin):
    fieldsets = (
        ("Employee identity", {"fields": ("username", "first_name", "last_name", "email", "referral_code", "is_active")}),
        (
            "Assignment control",
            {
                "fields": (
                    ("assignment_status", "demo_progress", "client_progress"),
                    "client_activated_at",
                    "carried_demo_earnings",
                    ("demo_earnings", "client_earnings", "total_earnings"),
                )
            },
        ),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (("Employee identity", {"fields": ("email", "first_name", "last_name", "referral_code")}),)
    readonly_fields = (
        "client_activated_at",
        "carried_demo_earnings",
        "demo_earnings",
        "client_earnings",
        "total_earnings",
        "last_login",
        "date_joined",
    )
    list_display = (
        "employee_name",
        "email",
        "referral_code",
        "assignment_status",
        "demo_progress",
        "client_progress",
        "demo_earnings",
        "client_earnings",
        "total_earnings",
    )
    list_display_links = ("employee_name",)
    list_editable = ("referral_code", "assignment_status", "demo_progress", "client_progress")
    list_filter = (AssignmentStatusFilter, "is_active", "is_staff")
    search_fields = ("first_name", "last_name", "email", "referral_code")
    ordering = ("first_name", "last_name", "email")
    list_per_page = 25
    actions = ("activate_client_accounts",)

    class Media:
        css = {"all": ("admin/control_panel.css",)}

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("assignment_lots")

    @admin.display(description="Name", ordering="first_name")
    def employee_name(self, obj):
        return obj.full_name or obj.username

    def _summary(self, obj, assignment_type):
        return assignment_summary(obj, assignment_type)

    @admin.display(description="Demo earnings")
    def demo_earnings(self, obj):
        return f"${self._summary(obj, AssignmentLot.AssignmentType.DEMO)['current_earnings']:.2f}"

    @admin.display(description="Client earnings")
    def client_earnings(self, obj):
        return f"${self._summary(obj, AssignmentLot.AssignmentType.CLIENT)['current_earnings']:.2f}"

    @admin.display(description="Total earnings")
    def total_earnings(self, obj):
        demo = self._summary(obj, AssignmentLot.AssignmentType.DEMO)["current_earnings"]
        client = self._summary(obj, AssignmentLot.AssignmentType.CLIENT)["current_earnings"]
        carried = obj.carried_demo_earnings if obj.client_is_active else demo
        return f"${carried + client:.2f}"

    def save_model(self, request, obj, form, change):
        previous = None
        if change:
            previous = ClientUser.objects.filter(pk=obj.pk).values("demo_progress", "client_progress", "assignment_status").first()
        super().save_model(request, obj, form, change)
        if not change:
            create_default_lots(obj)
            return
        if previous["demo_progress"] != obj.demo_progress:
            set_progress(
                obj,
                AssignmentLot.AssignmentType.DEMO,
                obj.demo_progress,
                changed_by=request.user,
                previous_progress=previous["demo_progress"],
            )
        if previous["client_progress"] != obj.client_progress:
            set_progress(
                obj,
                AssignmentLot.AssignmentType.CLIENT,
                obj.client_progress,
                changed_by=request.user,
                previous_progress=previous["client_progress"],
            )
        if previous["assignment_status"] != obj.assignment_status:
            set_assignment_status(obj, obj.assignment_status, changed_by=request.user)

    @admin.action(description="Activate selected client accounts")
    def activate_client_accounts(self, request, queryset):
        activated = 0
        unavailable = 0
        for employee in queryset:
            try:
                activate_client_account(employee, changed_by=request.user, require_completed=False)
                activated += 1
            except ValueError:
                unavailable += 1
        if activated:
            self.message_user(request, f"Activated {activated} client account(s).", messages.SUCCESS)
        if unavailable:
            self.message_user(
                request,
                f"{unavailable} account(s) could not be activated.",
                messages.WARNING,
            )

# Register your models here.
