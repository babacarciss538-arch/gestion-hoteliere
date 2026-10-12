from django.shortcuts import render
from accounts.permissions import role_required_for_write
from .forms import RoomForm
from .models import Room

# Consultation : réception et équipes housekeeping / maintenance.
# Création de chambre : Directeur (et Administrateur, toujours autorisé) uniquement.
@role_required_for_write(
    read_roles=[
        'DIRECTOR',
        'RECEPTIONIST',
        'HOUSEKEEPING_MGR',
        'HOUSEKEEPER',
        'MAINTENANCE_MGR',
        'TECHNICIAN',
    ],
    write_roles=['DIRECTOR'],
)
def room_list(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'rooms/list.html', {
        'rooms': Room.objects.all(),
        'form': form,
        'can_manage_rooms': request.user.is_superuser or request.user.role in ('ADMIN', 'DIRECTOR'),
        'show_room_rates': request.user.role not in ('HOUSEKEEPING_MGR', 'HOUSEKEEPER', 'MAINTENANCE_MGR', 'TECHNICIAN'),
    })