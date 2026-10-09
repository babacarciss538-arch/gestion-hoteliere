from django.shortcuts import render
from accounts.permissions import role_required
from .forms import CashSessionForm
from .models import CashSession

@role_required(['DIRECTOR', 'CASHIER', 'ACCOUNTANT', 'NIGHT_AUDITOR'])
def cashier_index(request):
    form = CashSessionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        session = form.save(commit=False)
        session.cashier = request.user
        session.save()
    return render(request, 'cashier/index.html', {'form': form, 'sessions': CashSession.objects.filter(cashier=request.user)})
