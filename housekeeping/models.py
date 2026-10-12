from django.conf import settings
from django.db import models
from django.utils import timezone

from rooms.models import Room


class TaskStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    IN_PROGRESS = 'IN_PROGRESS', 'En cours'
    COMPLETED = 'COMPLETED', 'Terminée'


class TaskPriority(models.TextChoices):
    LOW = 'LOW', 'Basse'
    NORMAL = 'NORMAL', 'Normale'
    HIGH = 'HIGH', 'Haute'
    URGENT = 'URGENT', 'Urgente'


class HousekeepingTask(models.Model):
    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='housekeeping_tasks',
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='housekeeping_tasks',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_housekeeping_tasks',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=120, default='Nettoyage de chambre')
    notes = models.TextField(blank=True)
    priority = models.CharField(
        max_length=20,
        choices=TaskPriority.choices,
        default=TaskPriority.NORMAL,
    )
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-pk']

    def __str__(self):
        return f'{self.title} - {self.room or "Chambre non définie"}'


class HousekeepingTaskHistory(models.Model):
    task = models.ForeignKey(
        HousekeepingTask,
        on_delete=models.CASCADE,
        related_name='history',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='housekeeping_task_history',
    )
    action = models.CharField(max_length=30)
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    details = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']
