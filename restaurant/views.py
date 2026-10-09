from django.shortcuts import render
from accounts.permissions import role_required
from .forms import RestaurantOrderForm
from .models import RestaurantOrder

@role_required(['DIRECTOR', 'RESTAURANT_MGR', 'WAITER', 'KITCHEN_MGR', 'COOK'])
def restaurant_index(request):
    form = RestaurantOrderForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'restaurant/index.html', {'form': form, 'orders': RestaurantOrder.objects.order_by('-created_at')[:50]})
