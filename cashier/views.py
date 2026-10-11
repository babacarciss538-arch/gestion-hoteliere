from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from django.utils import timezone
from accounts.permissions import role_required
from .forms import CashSessionCloseForm, CashSessionForm
from .models import CashDiscrepancy, CashSession

@role_required(['DIRECTOR', 'RECEPTIONIST', 'NIGHT_AUDITOR'])
def cashier_index(request):
    sessions = CashSession.objects.filter(cashier=request.user).order_by('-opened_at')
    form = CashSessionForm()
    close_form = CashSessionCloseForm()

    if request.method == 'POST' and request.POST.get('action') == 'close':
        with transaction.atomic():
            session = get_object_or_404(
                CashSession.objects.select_for_update(),
                pk=request.POST.get('session_id'),
                cashier=request.user,
                is_closed=False,
            )
            close_form = CashSessionCloseForm(request.POST, instance=session)
            if close_form.is_valid():
                session = close_form.save(commit=False)
                session.is_closed = True
                session.closed_at = timezone.now()
                session.save(update_fields=['closing_amount', 'is_closed', 'closed_at'])
                return redirect('cashier:index')
    elif request.method == 'POST':
        form = CashSessionForm(request.POST)
        if CashSession.objects.filter(cashier=request.user, is_closed=False).exists():
            form.add_error(None, 'Vous avez déjà une session de caisse ouverte.')
        elif form.is_valid():
            session = form.save(commit=False)
            session.cashier = request.user
            session.save()
            return redirect('cashier:index')

    return render(request, 'cashier/index.html', {
        'form': form,
        'close_form': close_form,
        'sessions': sessions,
        'discrepancies': CashDiscrepancy.objects.filter(
            session__cashier=request.user,
        ).select_related('session').order_by('-created_at'),
        'has_open_session': sessions.filter(is_closed=False).exists(),
    })
