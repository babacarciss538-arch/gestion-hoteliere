from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from .models import Expense, Invoice, Payment, Refund, Tax

INPUT = {'class': 'form-control glass-input'}


def _amount_widget(minimum='0.01'):
    return forms.NumberInput(attrs={**INPUT, 'min': minimum, 'step': '0.01'})


class PaymentForm(forms.ModelForm):
    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.none(),
        required=False,
        empty_label='Paiement non affecté à une facture',
        widget=forms.Select(attrs=INPUT),
    )

    class Meta:
        model = Payment
        fields = ['invoice', 'amount']
        widgets = {'amount': _amount_widget()}

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
        if invoice is not None and amount is not None and amount > invoice.balance:
            self.add_error('amount', 'Le paiement dépasse le solde calculé de cette facture.')
        return cleaned_data


class InvoiceForm(forms.ModelForm):
    taxes = forms.ModelMultipleChoiceField(
        queryset=Tax.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Taxes à appliquer',
        help_text='Seules les taxes actives avec un taux sont proposées. '
                  'Le montant de chaque taxe est calculé sur le montant hors taxe.',
    )

    class Meta:
        model = Invoice
        fields = ['customer_name', 'description', 'subtotal', 'taxes']
        labels = {
            'customer_name': 'Client',
            'description': 'Objet de la facture',
            'subtotal': 'Montant hors taxe',
        }
        widgets = {
            'customer_name': forms.TextInput(attrs=INPUT),
            'description': forms.TextInput(attrs=INPUT),
            'subtotal': _amount_widget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = True
        self.fields['taxes'].queryset = Tax.objects.filter(
            is_active=True, rate__isnull=False, rate__gt=0,
        ).order_by('name')

    def clean_subtotal(self):
        subtotal = self.cleaned_data['subtotal']
        if subtotal <= 0:
            raise ValidationError('Le montant hors taxe doit être supérieur à zéro.')
        return subtotal

    def save(self, commit=True):
        invoice = super().save(commit=False)
        taxes = list(self.cleaned_data.get('taxes') or [])
        invoice.tax_amount = Invoice.calculate_tax_amount(invoice.subtotal, taxes)
        invoice.amount = invoice.subtotal + invoice.tax_amount
        if commit:
            invoice.save()
            invoice.taxes.set(taxes)
        return invoice


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['label', 'category', 'amount']
        labels = {'label': 'Libellé', 'category': 'Catégorie', 'amount': 'Montant'}
        widgets = {
            'label': forms.TextInput(attrs=INPUT),
            'category': forms.TextInput(attrs=INPUT),
            'amount': _amount_widget(),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError('Le montant de la dépense doit être supérieur à zéro.')
        return amount


class TaxForm(forms.ModelForm):
    class Meta:
        model = Tax
        fields = ['name', 'rate', 'amount']
        labels = {
            'name': 'Nom de la taxe',
            'rate': 'Taux applicable (%)',
            'amount': 'Montant enregistré',
        }
        help_texts = {
            'rate': 'Renseigner un taux pour une taxe applicable aux factures (calcul automatique).',
            'amount': 'Renseigner un montant pour enregistrer une taxe déjà collectée ou payée '
                      '(jamais appliquée automatiquement à une facture).',
        }
        widgets = {
            'name': forms.TextInput(attrs=INPUT),
            'rate': forms.NumberInput(attrs={**INPUT, 'min': '0.01', 'max': '100', 'step': '0.01'}),
            'amount': _amount_widget('0'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rate'].required = False
        self.fields['amount'].required = False

    def clean(self):
        cleaned_data = super().clean()
        rate = cleaned_data.get('rate')
        amount = cleaned_data.get('amount')
        has_amount = amount not in (None, Decimal('0'), Decimal('0.00'))
        if rate is None and not has_amount:
            raise ValidationError('Renseignez soit un taux applicable, soit un montant enregistré.')
        if rate is not None and has_amount:
            raise ValidationError(
                'Une taxe est soit applicable (taux), soit enregistrée (montant), pas les deux.'
            )
        if rate is not None and not (Decimal('0') < rate <= Decimal('100')):
            self.add_error('rate', 'Le taux doit être compris entre 0 (exclu) et 100.')
        if amount is not None and amount < 0:
            self.add_error('amount', 'Le montant ne peut pas être négatif.')
        cleaned_data['amount'] = amount if amount is not None else Decimal('0.00')
        return cleaned_data


class RefundForm(forms.ModelForm):
    payment = forms.ModelChoiceField(
        queryset=Payment.objects.none(),
        widget=forms.Select(attrs=INPUT),
        label='Paiement à rembourser',
    )

    class Meta:
        model = Refund
        fields = ['payment', 'amount', 'reason']
        labels = {'amount': 'Montant remboursé', 'reason': 'Motif'}
        widgets = {
            'amount': _amount_widget(),
            'reason': forms.TextInput(attrs=INPUT),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment'].queryset = Payment.objects.order_by('-created_at')
        self.fields['payment'].label_from_instance = lambda payment: (
            f'Paiement #{payment.pk} - {payment.amount}'
            + (f' (facture #{payment.invoice_id})' if payment.invoice_id else '')
        )
        self.fields['reason'].required = True

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise ValidationError('Le montant du remboursement doit être supérieur à zéro.')
        return amount

    def clean(self):
        cleaned_data = super().clean()
        payment = cleaned_data.get('payment')
        amount = cleaned_data.get('amount')
        if payment is not None and amount is not None and amount > payment.refundable_amount:
            self.add_error(
                'amount',
                f'Le remboursement dépasse le montant remboursable de ce paiement '
                f'({payment.refundable_amount}).',
            )
        return cleaned_data