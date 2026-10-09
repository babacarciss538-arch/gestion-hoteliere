from django.conf import settings
from django.db import models
from django.utils import timezone


class CashSession(models.Model):
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cash_sessions')
    is_closed = models.BooleanField(default=False)
    opening_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    opened_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)


class CashDiscrepancy(models.Model):
    session = models.ForeignKey(CashSession, on_delete=models.CASCADE, related_name='discrepancies')
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def difference(self):
        return self.actual_amount - self.expected_amount
