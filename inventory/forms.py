from django import forms

from .models import Product, StockMovement


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'quantity', 'committed_quantity', 'reorder_level', 'alert_level']
        widgets = {field: forms.TextInput(attrs={'class': 'form-control glass-input'}) for field in fields}
        widgets.update({field: forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'}) for field in ['quantity', 'committed_quantity', 'reorder_level']})
        widgets['alert_level'] = forms.Select(attrs={'class': 'form-control glass-input'})


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'movement_type', 'quantity']
        labels = {'product': 'Produit', 'movement_type': 'Type de mouvement', 'quantity': 'Quantité'}
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control glass-input'}),
            'movement_type': forms.Select(attrs={'class': 'form-control glass-input'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0', 'step': '0.01'}),
        }

    def clean(self):
        cleaned = super().clean()
        movement_type = cleaned.get('movement_type')
        quantity = cleaned.get('quantity')
        if quantity is not None:
            if movement_type in ('IN', 'OUT') and quantity <= 0:
                self.add_error('quantity', 'La quantité doit être supérieure à zéro.')
            if movement_type == 'ADJUSTMENT' and quantity < 0:
                self.add_error('quantity', 'Le stock ajusté ne peut pas être négatif.')
        return cleaned