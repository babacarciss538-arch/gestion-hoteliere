from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import redirect, render

from .models import Product, StockAlertLevel, StockMovement
from .permissions import not_commercial_required, storekeeper_or_admin_required

# Types de mouvement (le modèle les définit comme choix texte : 'IN', 'OUT', 'ADJUSTMENT').
MOVEMENT_IN = 'IN'
MOVEMENT_OUT = 'OUT'
MOVEMENT_ADJUSTMENT = 'ADJUSTMENT'


def compute_alert_level(product):
    """Niveau d'alerte déduit de la quantité et du seuil de réapprovisionnement."""
    if product.quantity <= 0:
        return StockAlertLevel.OUT_OF_STOCK
    if product.reorder_level > 0 and product.quantity <= product.reorder_level:
        return StockAlertLevel.CRITICAL
    return StockAlertLevel.NORMAL


@login_required
@not_commercial_required
def product_list(request):
    # `category` est un simple champ texte : pas de select_related.
    products = Product.objects.order_by('name')
    return render(request, 'inventory/product_list.html', {'products': products})


@login_required
@storekeeper_or_admin_required
def product_create(request):
    try:
        from .forms import ProductForm
    except ImportError:
        ProductForm = None

    if request.method == 'POST' and ProductForm:
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Article ajouté au stock avec succès.")
            return redirect('inventory:product_list')
    else:
        form = ProductForm() if ProductForm else None

    return render(request, 'inventory/product_form.html', {'form': form})


@login_required
@not_commercial_required
def stock_alerts(request):
    """Articles en rupture ou ayant atteint leur seuil de réapprovisionnement."""
    out_of_stock = Product.objects.filter(quantity__lte=0).order_by('name')
    low_stock = Product.objects.filter(
        quantity__gt=0,
        quantity__lte=F('reorder_level'),
    ).order_by('name')
    return render(request, 'inventory/stock_alerts.html', {
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
    })


@login_required
@storekeeper_or_admin_required
def stock_movement_create(request):
    """Enregistre un mouvement réel de stock (entrée, sortie, ajustement)."""
    try:
        from .forms import StockMovementForm
    except ImportError:
        StockMovementForm = None

    if request.method == 'POST' and StockMovementForm:
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            with transaction.atomic():
                # Verrou sur le produit : deux mouvements simultanés ne s'écrasent pas.
                product = Product.objects.select_for_update().get(pk=movement.product_id)
                if movement.movement_type == MOVEMENT_IN:
                    product.quantity += movement.quantity
                elif movement.movement_type == MOVEMENT_OUT:
                    if movement.quantity > product.quantity:
                        form.add_error('quantity', f"Stock insuffisant : {product.quantity} disponible(s).")
                        product = None
                    else:
                        product.quantity -= movement.quantity
                elif movement.movement_type == MOVEMENT_ADJUSTMENT:
                    # Ajustement : la quantité saisie devient le nouveau stock physique.
                    product.quantity = movement.quantity

                if product is not None:
                    product.alert_level = compute_alert_level(product)
                    product.save(update_fields=['quantity', 'alert_level'])
                    movement.save()
                    messages.success(request, "Mouvement de stock enregistré.")
                    return redirect('inventory:product_list')
    else:
        form = StockMovementForm() if StockMovementForm else None

    return render(request, 'inventory/movement_form.html', {'form': form})