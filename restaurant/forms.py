from django import forms
from reception.models import CheckIn
from .models import MenuCategory, MenuItem, RestaurantOrder, PaymentType


class RestaurantOrderCreateForm(forms.ModelForm):
    class Meta:
        model = RestaurantOrder
        fields = ['table_number', 'payment_type', 'check_in', 'notes']
        widgets = {
            'table_number': forms.TextInput(attrs={
                'class': 'form-control glass-input',
                'placeholder': 'Ex: T-01, T-12, Terrasse...',
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-select glass-input',
                'id': 'id_payment_type',
                'onchange': 'toggleCheckInField()',
            }),
            'check_in': forms.Select(attrs={
                'class': 'form-select glass-input',
                'id': 'id_check_in',
            }),
            'notes': forms.TextInput(attrs={
                'class': 'form-control glass-input',
                'placeholder': 'Ex: Sans sel, cuisson à point...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ne proposer que les séjours actuellement en cours (arrivés et non partis)
        active_stays = CheckIn.objects.filter(
            actual_check_in__isnull=False,
            actual_check_out__isnull=True,
            reservation__isnull=False,
        ).select_related('reservation__guest', 'reservation__room').order_by('reservation__room__number')
        self.fields['check_in'].queryset = active_stays
        self.fields['check_in'].empty_label = 'Sélectionner la chambre cliente hébergée...'
        self.fields['check_in'].required = False

    def clean(self):
        cleaned_data = super().clean()
        payment_type = cleaned_data.get('payment_type')
        check_in = cleaned_data.get('check_in')

        if payment_type == PaymentType.ROOM:
            if not check_in:
                self.add_error('check_in', 'Veuillez sélectionner la chambre cliente pour imputer la note.')
            elif check_in.actual_check_out is not None:
                self.add_error('check_in', 'Ce client a déjà effectué son Check-Out. Imputation impossible.')
        return cleaned_data


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'price', 'description', 'is_available']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select glass-input'}),
            'name': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'price': forms.NumberInput(attrs={'class': 'form-control glass-input', 'step': '100'}),
            'description': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 2}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }