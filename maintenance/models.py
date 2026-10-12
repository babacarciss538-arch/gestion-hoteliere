from django.conf import settings
from django.db import models
from django.utils import timezone


class TicketPriority(models.TextChoices):
    LOW = 'LOW', 'Basse'
    NORMAL = 'NORMAL', 'Normale'
    HIGH = 'HIGH', 'Haute'
    CRITICAL = 'CRITICAL', 'Urgence / Bloquante'


class TicketStatus(models.TextChoices):
    OPEN = 'OPEN', 'Signalé (Ouvert)'
    ASSIGNED = 'ASSIGNED', 'Assigné au technicien'
    IN_PROGRESS = 'IN_PROGRESS', 'Intervention en cours'
    WAITING_PART = 'WAITING_PART', 'En attente de pièce / matériel'
    RESOLVED = 'RESOLVED', 'Résolu — En attente de validation'
    CLOSED = 'CLOSED', 'Clôturé (Validé)'


class TechnicianType(models.TextChoices):
    INTERNAL = 'INTERNAL', 'Technicien interne'
    EXTERNAL = 'EXTERNAL', 'Prestataire externe'


class MaintenanceTicket(models.Model):
    # ── Identification ──────────────────────────────────────────────────────
    title = models.CharField('Intitulé du problème', max_length=200, default='Incident technique')
    description = models.CharField('Description du problème', max_length=255, blank=True)
    location = models.CharField('Emplacement / Chambre', max_length=120, blank=True)
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='maintenance_tickets',
        verbose_name='Chambre concernée',
    )

    # ── Qualification ───────────────────────────────────────────────────────
    priority = models.CharField(
        'Priorité', max_length=20,
        choices=TicketPriority.choices,
        default=TicketPriority.NORMAL,
    )
    status = models.CharField(
        'Statut', max_length=20,
        choices=TicketStatus.choices,
        default=TicketStatus.OPEN,
    )

    # ── Acteurs ─────────────────────────────────────────────────────────────
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reported_tickets',
        verbose_name='Signalé par',
    )
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_maintenance_tickets',
        verbose_name='Technicien interne affecté',
    )

    # ── Technicien externe ──────────────────────────────────────────────────
    technician_type = models.CharField(
        'Type de technicien',
        max_length=20,
        choices=TechnicianType.choices,
        default=TechnicianType.INTERNAL,
    )
    external_company = models.CharField(
        'Société prestataire externe',
        max_length=150,
        blank=True,
    )
    external_contact = models.CharField(
        'Contact prestataire (nom / téléphone)',
        max_length=150,
        blank=True,
    )

    # ── Résolution ──────────────────────────────────────────────────────────
    resolution_notes = models.TextField('Notes de résolution technique', blank=True)

    # ── Horodatage ──────────────────────────────────────────────────────────
    created_at = models.DateTimeField('Signalé le', default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_at = models.DateTimeField('Affecté le', null=True, blank=True)
    resolved_at = models.DateTimeField('Résolu le', null=True, blank=True)
    closed_at = models.DateTimeField('Clôturé le', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket Maintenance'
        verbose_name_plural = 'Tickets Maintenance'

    def __str__(self):
        return f'[{self.get_priority_display()}] {self.title} — {self.get_status_display()}'

    @property
    def is_open(self):
        return self.status not in (TicketStatus.RESOLVED, TicketStatus.CLOSED)

    def get_priority_badge(self):
        return {
            'LOW': 'secondary',
            'NORMAL': 'info',
            'HIGH': 'warning',
            'CRITICAL': 'danger',
        }.get(self.priority, 'secondary')

    def get_status_badge(self):
        return {
            'OPEN': 'danger',
            'ASSIGNED': 'warning',
            'IN_PROGRESS': 'primary',
            'WAITING_PART': 'secondary',
            'RESOLVED': 'success',
            'CLOSED': 'dark',
        }.get(self.status, 'secondary')


class MaintenanceTicketHistory(models.Model):
    ticket = models.ForeignKey(
        MaintenanceTicket,
        on_delete=models.CASCADE,
        related_name='history',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='maintenance_history_entries',
    )
    action = models.CharField(max_length=40)          # REPORTED, ASSIGNED, STARTED, RESOLVED, CLOSED, …
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    details = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.ticket} — {self.action}'
