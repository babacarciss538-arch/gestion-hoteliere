from django.shortcuts import render
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'ACCOUNTANT', 'NIGHT_AUDITOR'])
def reports_index(request):
    return render(request, 'reports/index.html')
