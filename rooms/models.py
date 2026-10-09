from django.db import models


class RoomStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Disponible'
    OCCUPIED = 'OCCUPIED', 'Occupée'
    RESERVED = 'RESERVED', 'Réservée'
    TO_CLEAN = 'TO_CLEAN', 'À nettoyer'
    MAINTENANCE = 'MAINTENANCE', 'Maintenance'


class Room(models.Model):
    number = models.CharField(max_length=20, unique=True)
    floor = models.CharField(max_length=50, blank=True)
    room_type = models.CharField(max_length=100, blank=True)
    nightly_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=RoomStatus.choices, default=RoomStatus.AVAILABLE)

    def __str__(self):
        return self.number