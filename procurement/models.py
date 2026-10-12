from django.db import models
from django.conf import settings
from inventory.models import Product, StockMovement


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        CONTACTED = 'CONTACTED', 'Fournisseur contacté'
        PENDING = 'PENDING', 'En attente'
        RECEIVED = 'RECEIVED', 'Commande reçue'
        DELIVERED = 'DELIVERED', 'Commande livrée'

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"PO #{self.id} - {self.supplier.name} ({self.get_status_display()})"

    def receive_order(self, user):
        """Valide la réception physique et incrémente le stock réel via un StockMovement de type IN."""
        if self.status in [self.Status.RECEIVED, self.Status.DELIVERED]:
            return False, "Cette commande a déjà été enregistrée comme reçue ou livrée."

        for item in self.items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()

            StockMovement.objects.create(
                product=item.product,
                movement_type=StockMovement.MovementType.IN,
                quantity=item.quantity,
                reason=f"Réception Commande d'Approvisionnement #{self.id}",
                created_by=user
            )

        self.status = self.Status.DELIVERED
        self.save()
        return True, "Les stocks ont été mis à jour avec succès suite à la réception."


# Rétrocompatibilité avec les vues/dashboard
PurchaseOrderStatus = PurchaseOrder.Status


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Delivery(models.Model):
    """Modèle d'enregistrement des livraisons pour rétrocompatibilité."""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='deliveries')
    delivery_date = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Livraison #{self.id} pour PO #{self.purchase_order_id}"


class SupplyRequest(models.Model):
    """Demande de réapprovisionnement / besoin émise par le Chef Cuisinier."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        APPROVED = 'APPROVED', 'Approuvée'
        REJECTED = 'REJECTED', 'Rejetée'

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='supply_requests')
    requested_quantity = models.PositiveIntegerField()
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Demande #{self.id} - {self.product.name} ({self.requested_quantity}) par {self.requested_by}"