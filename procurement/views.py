from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PurchaseOrder, Supplier, SupplyRequest
from .forms import SupplierForm, PurchaseOrderForm, SupplyRequestForm
from inventory.permissions import not_commercial_required, storekeeper_or_admin_required


@login_required
@not_commercial_required
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'procurement/supplier_list.html', {'suppliers': suppliers})


@login_required
@storekeeper_or_admin_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fournisseur créé avec succès.")
            return redirect('procurement:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'procurement/supplier_form.html', {'form': form})


@login_required
@not_commercial_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.all().select_related('supplier', 'created_by').order_by('-order_date')
    return render(request, 'procurement/purchase_order_list.html', {'orders': orders})


@login_required
@storekeeper_or_admin_required
def purchase_order_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            messages.success(request, "Commande créée avec succès.")
            return redirect('procurement:purchase_order_list')
    else:
        form = PurchaseOrderForm()
    return render(request, 'procurement/purchase_order_form.html', {'form': form})


@login_required
@storekeeper_or_admin_required
def receive_purchase_order(request, order_id):
    """Validation physique de la réception : Incrémente réellement le stock."""
    order = get_object_or_404(PurchaseOrder, id=order_id)
    if request.method == 'POST':
        success, message = order.receive_order(request.user)
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)
        return redirect('procurement:purchase_order_list')
    return render(request, 'procurement/confirm_receipt.html', {'order': order})


@login_required
@not_commercial_required
def supply_request_list(request):
    """Affiche les demandes de réapprovisionnement transmises par la cuisine."""
    requests = SupplyRequest.objects.all().select_related('product', 'requested_by').order_by('-created_at')
    return render(request, 'procurement/supply_request_list.html', {'requests': requests})


@login_required
@not_commercial_required
def create_supply_request(request):
    """Permet au Chef Cuisinier d'émettre une demande de réapprovisionnement."""
    if request.method == 'POST':
        form = SupplyRequestForm(request.POST)
        if form.is_valid():
            supply_req = form.save(commit=False)
            supply_req.requested_by = request.user
            supply_req.save()
            messages.success(request, "Votre demande de réapprovisionnement a été transmise au magasinier.")
            return redirect('procurement:supply_request_list')
    else:
        form = SupplyRequestForm()
    return render(request, 'procurement/supply_request_form.html', {'form': form})