from django.conf import settings
from django.db import models


class Task(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("FINISHED", "Finished"),
        ("FAILED", "Failed"),
    ]
    # Владелец: задачу видит и получает только он (фильтр — в web/services.py).
    # null=True — только для задач, созданных до появления владельца; они не видны никому.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
    )
    name = models.CharField(max_length=255)
    params = models.JSONField(default=dict)
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="PENDING",
    )
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task #{self.id} ({self.name}) - {self.status}"