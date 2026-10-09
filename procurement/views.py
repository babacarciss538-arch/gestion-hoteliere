from django.shortcuts import render
from accounts.permissions import role_required
from .forms import PurchaseOrderForm, SupplierForm
from .models import PurchaseOrder, Supplier

@role_required(['DIRECTOR', 'STOREKEEPER', 'COMMERCIAL_MGR'])
def procurement_list(request):
    order_form = PurchaseOrderForm(request.POST or None, prefix='order')
    supplier_form = SupplierForm(request.POST or None, prefix='supplier')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'supplier' and supplier_form.is_valid():
            supplier_form.save()
        elif action == 'order' and order_form.is_valid():
            order_form.save()

    return render(request, 'procurement/list.html', {
        'order_form': order_form,
        'supplier_form': supplier_form,
        'orders': PurchaseOrder.objects.select_related('supplier').order_by('-created_at'),
        'suppliers': Supplier.objects.filter(is_active=True),
    })
