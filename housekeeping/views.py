from django.shortcuts import render
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'HOUSEKEEPING_MGR', 'HOUSEKEEPER'])
def housekeeping_list(request):
    return render(request, 'housekeeping/list.html')
