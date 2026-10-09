from django import forms
from .models import Reservation


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['guest', 'room', 'check_in_date', 'check_out_date', 'status']
        widgets = {
            'guest': forms.Select(attrs={'class': 'form-control glass-input'}),
            'room': forms.Select(attrs={'class': 'form-control glass-input'}),
            'check_in_date': forms.DateInput(attrs={'class': 'form-control glass-input', 'type': 'date'}),
            'check_out_date': forms.DateInput(attrs={'class': 'form-control glass-input', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control glass-input'}),
        }