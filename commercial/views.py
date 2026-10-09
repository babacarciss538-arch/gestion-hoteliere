from django.shortcuts import render
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'COMMERCIAL_MGR'])
def commercial_index(request):
    return render(request, 'commercial/index.html')
