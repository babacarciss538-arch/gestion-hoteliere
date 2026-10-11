from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from accounts.permissions import role_required
from cashier.models import CashSession
from .forms import PaymentForm
from .models import Expense, Invoice, Payment, Refund, Tax

@role_required(['DIRECTOR', 'RECEPTIONIST', 'NIGHT_AUDITOR'])
def finance_index(request):
    payment_form = PaymentForm()
    if request.method == 'POST':
        payment_form = PaymentForm(request.POST)
        with transaction.atomic():
            cash_session = CashSession.objects.select_for_update().filter(
                cashier=request.user,
                is_closed=False,
            ).first()
            if cash_session is None:
                payment_form.add_error(None, 'Ouvrez votre session de caisse avant d’enregistrer un paiement.')
            elif payment_form.is_valid():
                payment = payment_form.save(commit=False)
                if payment.invoice_id:
                    invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
                    paid_amount = Decimal('0.00')
                    for existing_payment in invoice.payments.prefetch_related('refunds'):
                        refunded_amount = sum(
                            (refund.amount for refund in existing_payment.refunds.all()),
                            Decimal('0.00'),
                        )
                        paid_amount += existing_payment.amount - refunded_amount
                    if paid_amount + payment.amount > invoice.amount:
                        payment_form.add_error('amount', 'Le paiement dépasse le solde calculé de cette facture.')
                    else:
                        payment.cash_session = cash_session
                        payment.save()
                        messages.success(request, 'Paiement enregistré dans votre session de caisse.')
                        return redirect('finance:index')
                else:
                    payment.cash_session = cash_session
                    payment.save()
                    messages.success(request, 'Paiement enregistré dans votre session de caisse.')
                    return redirect('finance:index')

    return render(request, 'finance/index.html', {
        'invoices': Invoice.objects.order_by('-created_at'),
        'payments': Payment.objects.order_by('-created_at'),
        'expenses': Expense.objects.order_by('-created_at'),
        'taxes': Tax.objects.order_by('-created_at'),
        'refunds': Refund.objects.select_related('payment').order_by('-created_at'),
        'payment_form': payment_form,
        'active_cash_session': CashSession.objects.filter(
            cashier=request.user,
            is_closed=False,
        ).first(),
    })
