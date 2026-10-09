from django import forms

from .models import PurchaseOrder, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control glass-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-control glass-input'}),
        }


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'reference', 'amount', 'status']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control glass-input'}),
            'reference': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control glass-input'}),
        }