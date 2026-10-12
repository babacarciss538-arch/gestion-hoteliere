from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models

ZERO = Decimal('0.00')
CENT = Decimal('0.01')


def _money(value):
    """Arrondit un montant à 2 décimales (arrondi commercial)."""
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


class Tax(models.Model):
    """Taxe.

    - Taxe applicable : `rate` renseigné (en %). Elle peut être cochée lors de
      la création d'une facture et son montant est alors calculé automatiquement.
    - Taxe enregistrée : `rate` vide et `amount` renseigné. C'est un simple
      enregistrement comptable (ex. taxe déjà collectée/payée) : elle n'est
      JAMAIS appliquée automatiquement à une facture.
    """
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_applicable(self):
        return self.is_active and self.rate is not None and self.rate > 0

    def __str__(self):
        if self.rate is not None:
            return f'{self.name} ({self.rate}%)'
        return self.name


class Invoice(models.Model):
    """Facture.

    `amount` reste le montant total dû (TTC). Pour une facture créée par le
    formulaire : amount = subtotal + tax_amount.
    Les anciennes factures ont subtotal = amount et tax_amount = 0.
    """
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxes = models.ManyToManyField(Tax, blank=True, related_name='invoices')
    customer_name = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def calculate_tax_amount(subtotal, taxes):
        """Règle de calcul : chaque taxe applicable = subtotal x taux / 100,
        arrondie au centime ; les taxes sans taux ou inactives sont ignorées."""
        subtotal = Decimal(subtotal)
        total = ZERO
        for tax in taxes:
            if tax.is_applicable:
                total += _money(subtotal * tax.rate / Decimal('100'))
        return total

    @property
    def paid_amount(self):
        """Paiements affectés à la facture, remboursements déduits."""
        total = ZERO
        for payment in self.payments.all():
            total += payment.amount - payment.refunded_amount
        return total

    @property
    def balance(self):
        return self.amount - self.paid_amount

    @property
    def status_label(self):
        paid = self.paid_amount
        if paid <= 0:
            return 'Impayée'
        if paid < self.amount:
            return 'Partiellement payée'
        return 'Payée'


class PaymentSource(models.TextChoices):
    ROOMS = 'ROOMS', 'Chambres & Hébergement'
    RESTAURANT = 'RESTAURANT', 'Restaurant & Bar'
    POOL = 'POOL', 'Piscine & Loisirs'
    SEMINAR = 'SEMINAR', 'Salles de séminaire & Événements'
    OTHER = 'OTHER', 'Autre'


class Payment(models.Model):
    source = models.CharField(
        max_length=20,
        choices=PaymentSource.choices,
        default=PaymentSource.ROOMS,
        verbose_name='Source de paiement',
    )
    payment_method = models.CharField(
        max_length=30,
        default='CASH',
        verbose_name='Moyen de paiement',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    invoice = models.ForeignKey(
        'finance.Invoice',
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,
        blank=True,
    )
    cash_session = models.ForeignKey(
        'cashier.CashSession',
        on_delete=models.PROTECT,
        related_name='payments',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    @property
    def refunded_amount(self):
        return sum((refund.amount for refund in self.refunds.all()), ZERO)

    @property
    def refundable_amount(self):
        return self.amount - self.refunded_amount


class Expense(models.Model):
    label = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    category = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Refund(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)