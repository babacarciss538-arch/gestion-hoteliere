from django import forms

from accounts.models import UserRole
from accounts.models import User
from rooms.models import Room, RoomStatus

from .models import HousekeepingTask, TaskPriority


class HousekeepingAssignmentForm(forms.ModelForm):
    class Meta:
        model = HousekeepingTask
        fields = ['room', 'assigned_to', 'priority', 'notes']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-control glass-input'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control glass-input'}),
            'priority': forms.Select(attrs={'class': 'form-control glass-input'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control glass-input',
                'rows': 3,
                'placeholder': 'Consignes particulières (facultatif)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(status=RoomStatus.TO_CLEAN).order_by('number')
        self.fields['assigned_to'].queryset = User.objects.filter(
            role=UserRole.HOUSEKEEPER,
            is_active=True,
        ).order_by('last_name', 'first_name', 'email')
        self.fields['room'].empty_label = 'Choisir une chambre à nettoyer'
        self.fields['assigned_to'].empty_label = 'Choisir une femme de chambre'
        self.fields['priority'].choices = TaskPriority.choices
        self.fields['room'].required = True
        self.fields['assigned_to'].required = True