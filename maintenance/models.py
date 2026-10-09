from django.db import models


class TicketStatus(models.TextChoices):
    OPEN = 'OPEN', 'Ouvert'
    ASSIGNED = 'ASSIGNED', 'Assigné'
    CLOSED = 'CLOSED', 'Fermé'


class MaintenanceTicket(models.Model):
    description = models.CharField(max_length=255, blank=True)
    priority = models.CharField(max_length=20, default='NORMAL')
    location = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
