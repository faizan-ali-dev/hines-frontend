from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class TaskDefinition(models.Model):
    class AssignmentType(models.TextChoices):
        DEMO = "demo", "Demo"
        CLIENT = "client", "Client"

    assignment_type = models.CharField(max_length=10, choices=AssignmentType.choices)
    lot_number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    task_name = models.CharField(max_length=150)
    task_description = models.TextField(blank=True)
    task_value = models.DecimalField(max_digits=12, decimal_places=2)
    employee_earning = models.DecimalField(max_digits=12, decimal_places=2)
    task_link = models.URLField(blank=True)

    class Meta:
        ordering = ("assignment_type", "lot_number")
        constraints = [
            models.UniqueConstraint(
                fields=("assignment_type", "lot_number"),
                name="unique_assignment_type_lot_number",
            )
        ]

    def __str__(self):
        return f"{self.get_assignment_type_display()} #{self.lot_number:03d} {self.task_name}"


class AssignmentLot(models.Model):
    """An individual employee's completion state for a shared task definition."""

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_lots")
    task_definition = models.ForeignKey(TaskDefinition, blank=True, null=True, on_delete=models.CASCADE, related_name="assignments")
    assignment_type = models.CharField(max_length=10, choices=TaskDefinition.AssignmentType.choices)
    lot_number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    task_name = models.CharField(max_length=150)
    task_description = models.TextField(blank=True)
    task_value = models.DecimalField(max_digits=12, decimal_places=2)
    employee_earning = models.DecimalField(max_digits=12, decimal_places=2)
    task_link = models.URLField(blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ("assignment_type", "lot_number")
        constraints = [
            models.UniqueConstraint(
                fields=("employee", "assignment_type", "lot_number"),
                name="unique_employee_assignment_lot",
            ),
            models.UniqueConstraint(
                fields=("employee", "task_definition"),
                name="unique_employee_task_definition",
            ),
        ]

    def __str__(self):
        return f"{self.employee.email} {self.assignment_type} #{self.lot_number:03d}"


class ProgressChange(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress_changes")
    assignment_type = models.CharField(max_length=10, choices=TaskDefinition.AssignmentType.choices)
    previous_progress = models.PositiveSmallIntegerField()
    new_progress = models.PositiveSmallIntegerField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="progress_changes_made",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.employee.email}: {self.assignment_type} {self.previous_progress}→{self.new_progress}"

# Create your models here.
