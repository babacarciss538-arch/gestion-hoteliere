from django import forms
from .models import CashSession


class CashSessionForm(forms.ModelForm):
    class Meta:
        model = CashSession
        fields = ['opening_amount']
        widgets = {'opening_amount': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'})}