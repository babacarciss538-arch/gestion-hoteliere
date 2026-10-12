from django.conf import settings
from django.db import models


class OrderStatus(models.TextChoices):
    RECEIVED = 'RECEIVED', 'Reçue (En attente)'
    PREPARING = 'PREPARING', 'En préparation'
    READY = 'READY', 'Terminée (Prête en cuisine)'
    SERVED = 'SERVED', 'Servie à table'
    CHARGED_TO_ROOM = 'CHARGED_TO_ROOM', 'Imputée sur Chambre (À régler au Check-Out)'
    PAID = 'PAID', 'Payée directement (Caisse / Cash / CB)'
    CANCELLED = 'CANCELLED', 'Annulée'


class PaymentType(models.TextChoices):
    DIRECT = 'DIRECT', 'Paiement direct (Caisse)'
    ROOM = 'ROOM', 'Imputation sur chambre (Note de séjour)'


class MenuCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom de la catégorie')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Catégorie Menu'
        verbose_name_plural = 'Catégories Menu'

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=150, verbose_name='Nom du plat / boisson')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Prix unitaire')
    description = models.TextField(blank=True, verbose_name='Description')
    is_available = models.BooleanField(default=True, verbose_name='Disponible')

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Article Menu'
        verbose_name_plural = 'Articles Menu'

    def __str__(self):
        return f"{self.name} ({self.price} FCFA)"


class RestaurantOrder(models.Model):
    table_number = models.CharField(max_length=20, blank=True, verbose_name='N° Table')
    server = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='server_orders',
        verbose_name='Serveur',
    )
    # Association chambre / séjour
    check_in = models.ForeignKey(
        'reception.CheckIn',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='restaurant_orders',
        verbose_name='Séjour / Chambre cliente',
    )
    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.DIRECT,
        verbose_name='Mode de règlement prévu',
    )
    status = models.CharField(
        max_length=25,
        choices=OrderStatus.choices,
        default=OrderStatus.RECEIVED,
        verbose_name='Statut de la commande',
    )
    notes = models.CharField(max_length=255, blank=True, verbose_name='Instructions de cuisson / service')
    description = models.CharField(max_length=255, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total (FCFA)')
    
    # Liens d'encaissement direct
    payment = models.ForeignKey(
        'finance.Payment',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='restaurant_orders',
        verbose_name='Paiement caisse',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Créée le')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Commande Restaurant'
        verbose_name_plural = 'Commandes Restaurant'

    def __str__(self):
        return f"Commande #{self.id} — Table {self.table_number or 'Room-Service'} — {self.total_amount} FCFA"

    @property
    def is_settled(self):
        """Vérifie si la commande est réellement soldée (soit payée, soit imputée)."""
        return self.status in (OrderStatus.PAID, OrderStatus.CHARGED_TO_ROOM)

    def recalculate_total(self):
        total = sum((item.subtotal for item in self.items.all()), 0)
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class OrderItem(models.Model):
    order = models.ForeignKey(RestaurantOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, verbose_name='Article')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantité')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Prix unitaire')

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        if not self.unit_price and self.item:
            self.unit_price = self.item.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.item.name} ({self.subtotal} FCFA)"