from django.shortcuts import render
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'KITCHEN_MGR', 'COOK'])
def kitchen_kds(request):
    return render(request, 'kitchen/kds.html')
