from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import Invoice, Payment


class PaymentForm(forms.ModelForm):
    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.none(),
        required=False,
        empty_label='Paiement non affecté à une facture',
        widget=forms.Select(attrs={'class': 'form-control glass-input'}),
    )

    class Meta:
        model = Payment
        fields = ['invoice', 'amount']
        widgets = {'amount': forms.NumberInput(attrs={
            'class': 'form-control glass-input',
            'min': '0.01',
            'step': '0.01',
        })}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['invoice'].queryset = Invoice.objects.order_by('-created_at')
        self.fields['invoice'].label_from_instance = lambda invoice: (
            f'Facture #{invoice.pk} - {invoice.amount}'
        )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError('Le montant du paiement doit être supérieur à zéro.')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        invoice = cleaned_data.get('invoice')
        amount = cleaned_data.get('amount')
        if invoice is None or amount is None:
            return cleaned_data

        paid_amount = Decimal('0.00')
        for payment in invoice.payments.prefetch_related('refunds'):
            refunded_amount = sum(
                (refund.amount for refund in payment.refunds.all()),
                Decimal('0.00'),
            )
            paid_amount += payment.amount - refunded_amount
        if paid_amount + amount > invoice.amount:
            self.add_error('amount', 'Le paiement dépasse le solde calculé de cette facture.')
        return cleaned_data