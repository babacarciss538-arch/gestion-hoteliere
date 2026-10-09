from django import forms
from .models import RestaurantOrder


class RestaurantOrderForm(forms.ModelForm):
    class Meta:
        model = RestaurantOrder
        fields = ['description', 'table_number', 'total_amount']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'table_number': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'}),
        }