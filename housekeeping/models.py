from django.db import models


class TaskStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    IN_PROGRESS = 'IN_PROGRESS', 'En cours'
    COMPLETED = 'COMPLETED', 'Terminée'


class HousekeepingTask(models.Model):
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
