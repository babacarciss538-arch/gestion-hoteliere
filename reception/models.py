from decimal import Decimal
from django.db import models


ZERO = Decimal('0.00')


class CheckIn(models.Model):
    reservation = models.OneToOneField(
        'reservations.Reservation',
        on_delete=models.PROTECT,
        related_name='check_in_record',
        null=True,
        blank=True,
    )
    actual_check_in = models.DateTimeField(null=True, blank=True, verbose_name='Arrivée effective')
    expected_check_out = models.DateField(null=True, blank=True, verbose_name='Départ prévu')
    actual_check_out = models.DateTimeField(null=True, blank=True, verbose_name='Départ effectif')

    class Meta:
        ordering = ['-actual_check_in']
        verbose_name = 'Séjour / Check-In'
        verbose_name_plural = 'Séjours / Check-Ins'

    def __str__(self):
        ch = self.reservation.room.number if (self.reservation and self.reservation.room) else 'Sans chambre'
        client = self.reservation.guest if self.reservation else 'Client'
        return f"Chambre {ch} — {client}"

    @property
    def room_number(self):
        return self.reservation.room.number if (self.reservation and self.reservation.room) else '-'

    @property
    def guest_name(self):
        return str(self.reservation.guest) if (self.reservation and self.reservation.guest) else 'Client'

    @property
    def room_charges(self):
        """Montant total estimé ou effectif de l'hébergement."""
        if not self.reservation or not self.reservation.room:
            return ZERO
        rate = self.reservation.room.nightly_rate or ZERO
        nights = 1
        if self.reservation.check_in_date and self.reservation.check_out_date:
            delta = (self.reservation.check_out_date - self.reservation.check_in_date).days
            nights = max(delta, 1)
        return rate * Decimal(nights)

    @property
    def restaurant_charges(self):
        """Total des consommations restaurant imputées sur cette chambre."""
        orders = self.restaurant_orders.filter(status='CHARGED_TO_ROOM')
        return sum((order.total_amount for order in orders), ZERO)

    @property
    def total_charges(self):
        """Montant total des prestations cumulées."""
        return self.room_charges + self.restaurant_charges
