from django import forms
from django.core.exceptions import ValidationError
from .models import CashSession


class CashSessionForm(forms.ModelForm):
    class Meta:
        model = CashSession
        fields = ['opening_amount']
        widgets = {'opening_amount': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'})}

    def clean_opening_amount(self):
        amount = self.cleaned_data['opening_amount']
        if amount < 0:
            raise ValidationError('Le fond initial doit être positif ou nul.')
        return amount


class CashSessionCloseForm(forms.ModelForm):
    class Meta:
        model = CashSession
        fields = ['closing_amount']
        widgets = {'closing_amount': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'})}

    def clean_closing_amount(self):
        amount = self.cleaned_data['closing_amount']
        if amount < 0:
            raise ValidationError('Le montant compté doit être positif ou nul.')
        return amount