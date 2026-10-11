from django.db import models


class Payment(models.Model):
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


class Invoice(models.Model):
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Expense(models.Model):
    label = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Tax(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Refund(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
