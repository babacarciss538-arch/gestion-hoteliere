from django.shortcuts import render
from accounts.permissions import role_required
from .forms import RoomForm
from .models import Room

@role_required([
    'DIRECTOR',
    'RECEPTIONIST',
    'BOOKING_AGENT',
    'HOUSEKEEPING_MGR',
    'HOUSEKEEPER',
    'MAINTENANCE_MGR',
    'TECHNICIAN',
])
def room_list(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'rooms/list.html', {'rooms': Room.objects.all(), 'form': form})
