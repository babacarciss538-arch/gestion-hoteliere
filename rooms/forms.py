from django import forms
from .models import Room


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['number', 'floor', 'room_type', 'nightly_rate', 'status']
        widgets = {field: forms.TextInput(attrs={'class': 'form-control glass-input'}) for field in fields}
        widgets = {
            **widgets,
            'nightly_rate': forms.NumberInput(attrs={'class': 'form-control glass-input', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control glass-input'}),
        }