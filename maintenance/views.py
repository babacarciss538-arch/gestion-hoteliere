from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User, UserRole
from accounts.permissions import enforce_read_only_for_admin_and_director, is_admin_or_director, role_required
from rooms.models import Room, RoomStatus

from .forms import MaintenanceAssignForm, MaintenanceReportForm, MaintenanceResolveForm
from .models import MaintenanceTicket, MaintenanceTicketHistory, TicketStatus, TechnicianType


# ── Helpers ──────────────────────────────────────────────────────────────────

# Seul le Responsable Maintenance a les droits d'écriture opérationnelle
MANAGER_ROLES = {UserRole.MAINTENANCE_MGR}


def _can_manage(user):
    """L'Administrateur et le Directeur sont strictement en lecture seule."""
    if is_admin_or_director(user):
        return False
    return user.role in MANAGER_ROLES


def _visible_tickets(user):
    """Le technicien ne voit que ses tickets ; le responsable et la direction voient tout."""
    qs = MaintenanceTicket.objects.select_related(
        'room', 'reported_by', 'assigned_technician',
    ).prefetch_related('history__actor')
    if user.role == UserRole.TECHNICIAN:
        qs = qs.filter(assigned_technician=user)
    return qs


# ── Tableau de bord principal ─────────────────────────────────────────────────

@role_required(['ADMIN', 'DIRECTOR', 'MAINTENANCE_MGR', 'TECHNICIAN'])
@enforce_read_only_for_admin_and_director
def maintenance_list(request):
    user = request.user
    can_manage = _can_manage(user)
    tickets = _visible_tickets(user)

    if request.method == 'POST' and can_manage:
        action = request.POST.get('action')
        if action == 'quick_assign':
            ticket_id = request.POST.get('ticket_id')
            ticket = get_object_or_404(MaintenanceTicket, pk=ticket_id)
            technician_type = request.POST.get('technician_type', 'INTERNAL')
            old_status = ticket.status

            with transaction.atomic():
                if technician_type == 'INTERNAL':
                    tech_id = request.POST.get('technician_id')
                    tech = get_object_or_404(User, pk=tech_id, role__in=[UserRole.TECHNICIAN, UserRole.MAINTENANCE_MGR])
                    ticket.technician_type = TechnicianType.INTERNAL
                    ticket.assigned_technician = tech
                    ticket.external_company = ''
                    ticket.external_contact = ''
                    details = f'Affecté à {tech.get_full_name() or tech.email}'
                else:
                    ext_company = request.POST.get('external_company', '').strip()
                    ext_contact = request.POST.get('external_contact', '').strip()
                    if not ext_company:
                        messages.error(request, 'Veuillez renseigner le nom du prestataire externe.')
                        return redirect('maintenance:list')
                    ticket.technician_type = TechnicianType.EXTERNAL
                    ticket.assigned_technician = None
                    ticket.external_company = ext_company
                    ticket.external_contact = ext_contact
                    details = f'Prestataire externe : {ext_company} ({ext_contact})'

                ticket.status = TicketStatus.ASSIGNED
                ticket.assigned_at = timezone.now()
                ticket.save()

                MaintenanceTicketHistory.objects.create(
                    ticket=ticket,
                    actor=user,
                    action='ASSIGNED',
                    from_status=old_status,
                    to_status=TicketStatus.ASSIGNED,
                    details=details,
                )

            messages.success(request, f'Incident #{ticket.id} affecté avec succès.')
            return redirect('maintenance:list')

    # Sous-ensembles pour les KPI
    open_tickets = tickets.filter(status=TicketStatus.OPEN)
    assigned_tickets = tickets.filter(status=TicketStatus.ASSIGNED)
    in_progress_tickets = tickets.filter(status=TicketStatus.IN_PROGRESS)
    resolved_tickets = tickets.filter(status=TicketStatus.RESOLVED)

    # Filtre par statut via GET
    status_filter = request.GET.get('status', '')
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    # Liste des techniciens disponibles pour le responsable
    available_technicians = User.objects.filter(
        role__in=[UserRole.TECHNICIAN, UserRole.MAINTENANCE_MGR],
        is_active=True,
    ).order_by('last_name', 'first_name')

    return render(request, 'maintenance/list.html', {
        'tickets': tickets,
        'can_manage': can_manage,
        'status_filter': status_filter,
        'status_choices': TicketStatus.choices,
        'available_technicians': available_technicians,
        'open_count': open_tickets.count(),
        'assigned_count': assigned_tickets.count(),
        'in_progress_count': in_progress_tickets.count(),
        'resolved_count': resolved_tickets.count(),
    })


# ── Signaler un incident ──────────────────────────────────────────────────────

@role_required(['ADMIN', 'DIRECTOR', 'MAINTENANCE_MGR', 'TECHNICIAN',
                'RECEPTIONIST', 'HOUSEKEEPING_MGR', 'HOUSEKEEPER'])
def maintenance_report(request):
    """Tout le personnel peut signaler un incident (sans champ Tarif)."""
    form = MaintenanceReportForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            ticket = form.save(commit=False)
            ticket.reported_by = request.user
            ticket.status = TicketStatus.OPEN
            ticket.save()
            # Si une chambre est liée, la passer en MAINTENANCE
            if ticket.room:
                room = Room.objects.select_for_update().get(pk=ticket.room_id)
                if room.status == RoomStatus.AVAILABLE:
                    room.status = RoomStatus.MAINTENANCE
                    room.save(update_fields=['status'])
            MaintenanceTicketHistory.objects.create(
                ticket=ticket,
                actor=request.user,
                action='REPORTED',
                to_status=TicketStatus.OPEN,
                details=f'Incident signalé : {ticket.title}',
            )
        messages.success(request, f'Ticket #{ticket.pk} créé — {ticket.title}')
        return redirect('maintenance:list')
    return render(request, 'maintenance/report.html', {'form': form})


# ── Détail + affecter / résoudre / clôturer ───────────────────────────────────

@role_required(['ADMIN', 'DIRECTOR', 'MAINTENANCE_MGR', 'TECHNICIAN'])
def maintenance_detail(request, pk):
    user = request.user
    can_manage = _can_manage(user)

    qs = MaintenanceTicket.objects.select_related(
        'room', 'reported_by', 'assigned_technician',
    ).prefetch_related('history__actor')
    # Technicien ne voit que ses tickets
    if user.role == UserRole.TECHNICIAN:
        ticket = get_object_or_404(qs, pk=pk, assigned_technician=user)
    else:
        ticket = get_object_or_404(qs, pk=pk)

    assign_form = MaintenanceAssignForm(instance=ticket) if can_manage else None
    resolve_form = MaintenanceResolveForm(instance=ticket)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── 1. Affecter un technicien ──────────────────────────────────────
        if action == 'assign' and can_manage:
            assign_form = MaintenanceAssignForm(request.POST, instance=ticket)
            if assign_form.is_valid():
                with transaction.atomic():
                    old_status = ticket.status
                    ticket = assign_form.save(commit=False)
                    ticket.status = TicketStatus.ASSIGNED
                    ticket.assigned_at = timezone.now()
                    ticket.save()
                    if ticket.technician_type == TechnicianType.INTERNAL:
                        details = f'Affecté à {ticket.assigned_technician.get_full_name() or ticket.assigned_technician.email}'
                    else:
                        details = f'Prestataire externe : {ticket.external_company} — {ticket.external_contact}'
                    MaintenanceTicketHistory.objects.create(
                        ticket=ticket,
                        actor=user,
                        action='ASSIGNED',
                        from_status=old_status,
                        to_status=TicketStatus.ASSIGNED,
                        details=details,
                    )
                messages.success(request, 'Technicien affecté — ticket passé à « Assigné ».')
                return redirect('maintenance:detail', pk=pk)

        # ── 2. Démarrer l'intervention (technicien) ────────────────────────
        elif action == 'start':
            if ticket.status != TicketStatus.ASSIGNED:
                messages.error(request, 'Ce ticket n\'est pas encore assigné.')
            else:
                with transaction.atomic():
                    old_status = ticket.status
                    ticket.status = TicketStatus.IN_PROGRESS
                    ticket.save(update_fields=['status', 'updated_at'])
                    MaintenanceTicketHistory.objects.create(
                        ticket=ticket,
                        actor=user,
                        action='STARTED',
                        from_status=old_status,
                        to_status=TicketStatus.IN_PROGRESS,
                        details='Intervention démarrée.',
                    )
                messages.success(request, 'Intervention démarrée.')
                return redirect('maintenance:detail', pk=pk)

        # ── 3. Renseigner la résolution (technicien → RESOLVED) ────────────
        elif action == 'resolve':
            resolve_form = MaintenanceResolveForm(request.POST, instance=ticket)
            if resolve_form.is_valid():
                with transaction.atomic():
                    old_status = ticket.status
                    ticket = resolve_form.save(commit=False)
                    if ticket.status == TicketStatus.RESOLVED:
                        ticket.resolved_at = timezone.now()
                    ticket.save()
                    MaintenanceTicketHistory.objects.create(
                        ticket=ticket,
                        actor=user,
                        action='RESOLVED' if ticket.status == TicketStatus.RESOLVED else 'UPDATED',
                        from_status=old_status,
                        to_status=ticket.status,
                        details=ticket.resolution_notes[:200] if ticket.resolution_notes else '',
                    )
                messages.success(request, 'Réparation enregistrée.')
                return redirect('maintenance:detail', pk=pk)

        # ── 4. Valider / Clôturer (responsable) ───────────────────────────
        elif action == 'close' and can_manage:
            if ticket.status != TicketStatus.RESOLVED:
                messages.error(request, 'Le ticket doit d\'abord être marqué Résolu.')
            else:
                with transaction.atomic():
                    old_status = ticket.status
                    ticket.status = TicketStatus.CLOSED
                    ticket.closed_at = timezone.now()
                    ticket.save(update_fields=['status', 'closed_at', 'updated_at'])
                    # Remettre la chambre Disponible si elle était en MAINTENANCE
                    if ticket.room and ticket.room.status == RoomStatus.MAINTENANCE:
                        ticket.room.status = RoomStatus.AVAILABLE
                        ticket.room.save(update_fields=['status'])
                    MaintenanceTicketHistory.objects.create(
                        ticket=ticket,
                        actor=user,
                        action='CLOSED',
                        from_status=old_status,
                        to_status=TicketStatus.CLOSED,
                        details='Réparation validée et ticket clôturé.',
                    )
                messages.success(request, 'Ticket clôturé — chambre remise Disponible.')
                return redirect('maintenance:list')

    return render(request, 'maintenance/detail.html', {
        'ticket': ticket,
        'assign_form': assign_form,
        'resolve_form': resolve_form,
        'can_manage': can_manage,
    })
