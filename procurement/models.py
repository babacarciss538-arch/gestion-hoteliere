from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Brouillon'
    ORDERED = 'ORDERED', 'Commandée'
    RECEIVED = 'RECEIVED', 'Reçue'
    CANCELLED = 'CANCELLED', 'Annulée'


class PurchaseOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    reference = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)


class Delivery(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='deliveries')
    delivered_at = models.DateTimeField(null=True, blank=True)
    is_received = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)