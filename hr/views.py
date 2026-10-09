from django.shortcuts import render
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'HR_MGR'])
def hr_index(request):
    return render(request, 'hr/index.html')
