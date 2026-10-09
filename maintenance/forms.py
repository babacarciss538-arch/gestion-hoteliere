from django import forms
from .models import MaintenanceTicket


class MaintenanceTicketForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTicket
        fields = ['description', 'location', 'priority']
        widgets = {field: forms.TextInput(attrs={'class': 'form-control glass-input'}) for field in fields}