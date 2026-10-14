from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


MAX_FAILED_ATTEMPTS = 4
LOCKOUT_SECONDS = 60


class LoginAttempt(models.Model):
    """
    Tracks failed login attempts per device (by IP address) so we can
    lock out a device for a short cooldown after too many failures —
    independent of which username/role was being tried, so it also
    protects against someone brute-forcing across different accounts.
    """

    ip_address = models.GenericIPAddressField(
        unique=True
    )

    failed_count = models.PositiveIntegerField(
        default=0
    )

    locked_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    @property
    def seconds_remaining(self):

        if not self.locked_until:
            return 0

        remaining = (self.locked_until - timezone.now()).total_seconds()

        return max(0, int(remaining))

    @property
    def is_locked(self):

        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_failure(self):

        self.failed_count += 1

        if self.failed_count >= MAX_FAILED_ATTEMPTS:
            self.locked_until = timezone.now() + timezone.timedelta(seconds=LOCKOUT_SECONDS)
            self.failed_count = 0

        self.save(update_fields=["failed_count", "locked_until", "updated_at"])

    def register_success(self):

        self.failed_count = 0
        self.locked_until = None
        self.save(update_fields=["failed_count", "locked_until", "updated_at"])

    def __str__(self):
        return f"{self.ip_address} — {self.failed_count} failed"


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