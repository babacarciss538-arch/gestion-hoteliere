from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'quantity', 'committed_quantity', 'reorder_level', 'alert_level']
        widgets = {field: forms.TextInput(attrs={'class': 'form-control glass-input'}) for field in fields}
        widgets.update({field: forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'}) for field in ['quantity', 'committed_quantity', 'reorder_level']})
        widgets['alert_level'] = forms.Select(attrs={'class': 'form-control glass-input'})