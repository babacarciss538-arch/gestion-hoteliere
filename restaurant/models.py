from django.db import models


class OrderStatus(models.TextChoices):
    OPEN = 'OPEN', 'Ouverte'
    PAID = 'PAID', 'Payée'
    CANCELLED = 'CANCELLED', 'Annulée'


class RestaurantOrder(models.Model):
    description = models.CharField(max_length=255, blank=True)
    table_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.OPEN)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)