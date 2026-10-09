from django.shortcuts import render
from accounts.permissions import role_required
from .forms import ReservationForm
from .models import Reservation

@role_required(['DIRECTOR', 'RECEPTIONIST', 'BOOKING_AGENT'])
def reservation_list(request):
    form = ReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'reservations/list.html', {'reservations': Reservation.objects.select_related('guest', 'room'), 'form': form})
