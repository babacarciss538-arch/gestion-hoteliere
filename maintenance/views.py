from django.shortcuts import render
from accounts.permissions import role_required
from .forms import MaintenanceTicketForm
from .models import MaintenanceTicket

@role_required(['DIRECTOR', 'MAINTENANCE_MGR', 'TECHNICIAN'])
def maintenance_list(request):
    form = MaintenanceTicketForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'maintenance/list.html', {'form': form, 'tickets': MaintenanceTicket.objects.all()})
