from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.permissions import role_required
from .forms import ReservationForm
from .models import Reservation

@role_required(['DIRECTOR', 'RECEPTIONIST'])
def reservation_list(request):
    form = ReservationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    query = request.GET.get('q', '').strip()
    reservations = Reservation.objects.select_related('guest', 'room')
    if query:
        reservations = reservations.filter(
            Q(reference__icontains=query)
            | Q(guest__first_name__icontains=query)
            | Q(guest__last_name__icontains=query)
            | Q(guest__email__icontains=query)
            | Q(room__number__icontains=query)
        )
    return render(request, 'reservations/list.html', {
        'reservations': reservations,
        'form': form,
        'query': query,
    })


@role_required(['DIRECTOR', 'RECEPTIONIST'])
def reservation_edit(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    form = ReservationForm(request.POST or None, instance=reservation)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('reservations:list')
    return render(request, 'reservations/edit.html', {
        'reservation': reservation,
        'form': form,
    })
