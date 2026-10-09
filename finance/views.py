from django.shortcuts import render
from accounts.permissions import role_required

@role_required(['DIRECTOR', 'ACCOUNTANT', 'CASHIER', 'NIGHT_AUDITOR'])
def finance_index(request):
    return render(request, 'finance/index.html')
