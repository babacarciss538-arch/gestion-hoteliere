from django.shortcuts import render
from accounts.permissions import role_required
from .forms import ProductForm
from .models import Product

@role_required(['DIRECTOR', 'STOREKEEPER', 'KITCHEN_MGR', 'COOK'])
def inventory_list(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'inventory/list.html', {'form': form, 'products': Product.objects.all()})
