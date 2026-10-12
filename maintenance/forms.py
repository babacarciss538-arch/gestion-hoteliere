from django import forms
from accounts.models import User, UserRole
from rooms.models import Room
from .models import MaintenanceTicket, TechnicianType


# ── Formulaire de signalement ────────────────────────────────────────────────
class MaintenanceReportForm(forms.ModelForm):
    """Tout utilisateur peut signaler un incident (pas de Tarif)."""

    class Meta:
        model = MaintenanceTicket
        fields = ['title', 'description', 'location', 'room', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control glass-input',
                'placeholder': 'Ex. : Climatisation chambre 204 hors service',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control glass-input',
                'rows': 3,
                'placeholder': 'Décrivez le problème en détail…',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control glass-input',
                'placeholder': 'Ex. : Salle de bain chambre 105, Hall d\'entrée…',
            }),
            'room': forms.Select(attrs={'class': 'form-select glass-input'}),
            'priority': forms.Select(attrs={'class': 'form-select glass-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(is_active=True).order_by('number')
        self.fields['room'].empty_label = 'Aucune chambre (zone commune)'
        self.fields['room'].required = False


# ── Formulaire d'affectation (responsable maintenance) ───────────────────────
class MaintenanceAssignForm(forms.ModelForm):
    """Permet d'affecter un technicien interne OU de saisir un prestataire externe."""

    class Meta:
        model = MaintenanceTicket
        fields = [
            'technician_type',
            'assigned_technician',
            'external_company',
            'external_contact',
        ]
        widgets = {
            'technician_type': forms.Select(attrs={
                'class': 'form-select glass-input',
                'id': 'id_technician_type',
                'onchange': 'toggleTechnicianFields()',
            }),
            'assigned_technician': forms.Select(attrs={
                'class': 'form-select glass-input',
                'id': 'id_assigned_technician',
            }),
            'external_company': forms.TextInput(attrs={
                'class': 'form-control glass-input',
                'placeholder': 'Nom de la société prestataire',
            }),
            'external_contact': forms.TextInput(attrs={
                'class': 'form-control glass-input',
                'placeholder': 'Nom du contact et téléphone',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_technician'].queryset = User.objects.filter(
            role__in=[UserRole.TECHNICIAN, UserRole.MAINTENANCE_MGR],
            is_active=True,
        ).order_by('last_name', 'first_name')
        self.fields['assigned_technician'].empty_label = 'Choisir un technicien interne…'
        self.fields['assigned_technician'].required = False
        self.fields['external_company'].required = False
        self.fields['external_contact'].required = False

    def clean(self):
        cleaned = super().clean()
        t_type = cleaned.get('technician_type')
        if t_type == TechnicianType.INTERNAL and not cleaned.get('assigned_technician'):
            self.add_error('assigned_technician', 'Sélectionnez un technicien interne.')
        if t_type == TechnicianType.EXTERNAL and not cleaned.get('external_company'):
            self.add_error('external_company', 'Saisissez le nom du prestataire externe.')
        return cleaned


# ── Formulaire de résolution ─────────────────────────────────────────────────
class MaintenanceResolveForm(forms.ModelForm):
    """Le technicien renseigne les notes de résolution et passe à RESOLVED."""

    class Meta:
        model = MaintenanceTicket
        fields = ['resolution_notes', 'status']
        widgets = {
            'resolution_notes': forms.Textarea(attrs={
                'class': 'form-control glass-input',
                'rows': 4,
                'placeholder': 'Décrivez la réparation effectuée, les pièces utilisées…',
            }),
            'status': forms.Select(attrs={'class': 'form-select glass-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le technicien ne peut passer qu'à RESOLVED ou WAITING_PART
        from .models import TicketStatus
        self.fields['status'].choices = [
            (TicketStatus.IN_PROGRESS, TicketStatus.IN_PROGRESS.label),
            (TicketStatus.WAITING_PART, TicketStatus.WAITING_PART.label),
            (TicketStatus.RESOLVED, TicketStatus.RESOLVED.label),
        ]