from django.shortcuts import render
from accounts.permissions import role_required
from .forms import GuestForm
from .models import Guest

@role_required(['DIRECTOR', 'RECEPTIONIST'])
def guest_list(request):
    form = GuestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'guests/list.html', {'guests': Guest.objects.all(), 'form': form})
