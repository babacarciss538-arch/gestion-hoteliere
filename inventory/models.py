from django.db import models


class StockAlertLevel(models.TextChoices):
    NORMAL = 'NORMAL', 'Normal'
    CRITICAL = 'CRITICAL', 'Critique'
    OUT_OF_STOCK = 'OUT_OF_STOCK', 'Rupture'


class Product(models.Model):
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True)
    alert_level = models.CharField(max_length=20, choices=StockAlertLevel.choices, default=StockAlertLevel.NORMAL)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    committed_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class StockMovement(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    movement_type = models.CharField(max_length=30, choices=[('IN', 'Entrée'), ('OUT', 'Sortie'), ('ADJUSTMENT', 'Ajustement')])
    created_at = models.DateTimeField(auto_now_add=True)


class ServiceRequest(models.Model):
    service = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_fulfilled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)