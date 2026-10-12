from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import role_required
from cashier.models import CashSession

from .forms import ExpenseForm, InvoiceForm, PaymentForm, RefundForm, TaxForm
from .models import Expense, Invoice, Payment, Refund, Tax

# Consultation et opérations courantes (l'Administrateur passe toujours par role_required).
FINANCE_ROLES = ['DIRECTOR', 'RECEPTIONIST', 'NIGHT_AUDITOR']
# Opérations financières sensibles : taxes et remboursements.
SENSITIVE_ROLES = ['DIRECTOR']


def _open_cash_session(user):
    return CashSession.objects.filter(cashier=user, is_closed=False).first()


@role_required(FINANCE_ROLES)
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
                    # Verrou sur la facture puis revalidation du solde (anti double encaissement).
                    invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
                    if payment.amount > invoice.balance:
                        payment_form.add_error('amount', 'Le paiement dépasse le solde calculé de cette facture.')
                        payment = None
                if payment is not None:
                    payment.cash_session = cash_session
                    payment.created_by = request.user
                    payment.save()
                    messages.success(request, 'Paiement enregistré dans votre session de caisse.')
                    return redirect('finance:index')

    return render(request, 'finance/index.html', {
        'invoices': Invoice.objects.prefetch_related('payments__refunds').order_by('-created_at'),
        'payments': Payment.objects.select_related('invoice').order_by('-created_at'),
        'expenses': Expense.objects.order_by('-created_at'),
        'taxes': Tax.objects.order_by('-created_at'),
        'refunds': Refund.objects.select_related('payment').order_by('-created_at'),
        'payment_form': payment_form,
        'active_cash_session': _open_cash_session(request.user),
        'can_manage_sensitive': request.user.is_superuser or request.user.role in (
            ['ADMIN'] + SENSITIVE_ROLES
        ),
    })


@role_required(FINANCE_ROLES)
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.prefetch_related('payments__refunds', 'taxes'), pk=pk,
    )
    return render(request, 'finance/invoice_detail.html', {'invoice': invoice})


@role_required(FINANCE_ROLES)
def invoice_create(request):
    form = InvoiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            form.save_m2m()
        messages.success(request, f'Facture #{invoice.pk} enregistrée.')
        return redirect('finance:invoice_detail', pk=invoice.pk)
    return render(request, 'finance/form.html', {
        'form': form,
        'title': 'Nouvelle facture',
        'submit_label': 'Enregistrer la facture',
    })


@role_required(FINANCE_ROLES)
def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        expense = form.save(commit=False)
        expense.created_by = request.user
        expense.save()
        messages.success(request, 'Dépense enregistrée.')
        return redirect('finance:index')
    return render(request, 'finance/form.html', {
        'form': form,
        'title': 'Nouvelle dépense',
        'submit_label': 'Enregistrer la dépense',
    })


@role_required(SENSITIVE_ROLES)
def tax_create(request):
    form = TaxForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tax = form.save(commit=False)
        tax.created_by = request.user
        tax.save()
        messages.success(request, 'Taxe enregistrée.')
        return redirect('finance:index')
    return render(request, 'finance/form.html', {
        'form': form,
        'title': 'Nouvelle taxe',
        'submit_label': 'Enregistrer la taxe',
    })


@role_required(SENSITIVE_ROLES)
def refund_create(request):
    form = RefundForm(request.POST or None)
    if request.method == 'POST':
        with transaction.atomic():
            if form.is_valid():
                # Verrou sur le paiement puis revalidation du montant remboursable.
                payment = Payment.objects.select_for_update().get(pk=form.cleaned_data['payment'].pk)
                if form.cleaned_data['amount'] > payment.refundable_amount:
                    form.add_error('amount', 'Le remboursement dépasse le montant remboursable de ce paiement.')
                else:
                    refund = form.save(commit=False)
                    refund.created_by = request.user
                    refund.save()
                    messages.success(request, 'Remboursement enregistré.')
                    return redirect('finance:index')
    return render(request, 'finance/form.html', {
        'form': form,
        'title': 'Nouveau remboursement',
        'submit_label': 'Enregistrer le remboursement',
    })