from django.db import models
from django.contrib.auth.models import User


class EmployeeMessage(models.Model):

    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="employee_messages"
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_read = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.employee.username} - {self.created_at}"

    class Meta:
        ordering = ["-created_at"]