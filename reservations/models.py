from django.db import models


class ReservationStatus(models.TextChoices):
    PENDING = 'PENDING', 'En attente'
    CONFIRMED = 'CONFIRMED', 'Confirmée'
    CANCELLED = 'CANCELLED', 'Annulée'
    COMPLETED = 'COMPLETED', 'Terminée'


class Reservation(models.Model):
    guest = models.ForeignKey('guests.Guest', on_delete=models.PROTECT, related_name='reservations', null=True, blank=True)
    room = models.ForeignKey('rooms.Room', on_delete=models.PROTECT, related_name='reservations', null=True, blank=True)
    reference = models.CharField(max_length=30, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.PENDING)
    check_in_date = models.DateField()
    check_out_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f'RES-{Reservation.objects.count() + 1:05d}'
        super().save(*args, **kwargs)
