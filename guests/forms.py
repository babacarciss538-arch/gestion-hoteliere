from django import forms
from .models import Guest


class GuestForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ['first_name', 'last_name', 'email', 'phone', 'nationality', 'identity_number']
        widgets = {field: forms.TextInput(attrs={'class': 'form-control glass-input'}) for field in fields}
        widgets = {
            **widgets,
            'email': forms.EmailInput(attrs={'class': 'form-control glass-input'}),
        }