from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import UserRole
from accounts.permissions import enforce_read_only_for_admin_and_director, is_admin_or_director, role_required
from rooms.models import Room, RoomStatus

from .forms import HousekeepingAssignmentForm
from .models import HousekeepingTask, HousekeepingTaskHistory, TaskStatus


# Rôles autorisés à créer / affecter des tâches (Seule la gouvernante a le pouvoir d'affecter)
ASSIGNMENT_ROLES = {UserRole.HOUSEKEEPING_MGR}


def _can_assign_tasks(user):
    """L'Administrateur et le Directeur sont en lecture seule stricte."""
    if is_admin_or_director(user):
        return False
    return user.role in ASSIGNMENT_ROLES


def _visible_tasks(user):
    """La femme de chambre ne voit que ses tâches ; la gouvernante et la direction voient tout."""
    qs = HousekeepingTask.objects.select_related('room', 'assigned_to', 'created_by')
    if user.role == UserRole.HOUSEKEEPER:
        qs = qs.filter(assigned_to=user)
    return qs.prefetch_related('history__actor')


@role_required(['ADMIN', 'DIRECTOR', 'HOUSEKEEPING_MGR', 'HOUSEKEEPER'])
@enforce_read_only_for_admin_and_director
def housekeeping_list(request):
    user = request.user
    can_assign = _can_assign_tasks(user)
    is_read_only = is_admin_or_director(user)
    form = HousekeepingAssignmentForm() if can_assign else None

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Affecter une nouvelle tâche ───────────────────────────────────────
        if action == 'assign':
            if not can_assign:
                raise PermissionDenied('Seule la gouvernante ou la direction peut affecter une tâche.')
            form = HousekeepingAssignmentForm(request.POST)
            if form.is_valid():
                with transaction.atomic():
                    room = Room.objects.select_for_update().get(pk=form.cleaned_data['room'].pk)
                    if room.status != RoomStatus.TO_CLEAN:
                        form.add_error('room', 'Cette chambre n\u2019est plus à nettoyer.')
                    else:
                        task = form.save(commit=False)
                        task.room = room
                        task.created_by = user
                        task.save()
                        HousekeepingTaskHistory.objects.create(
                            task=task,
                            actor=user,
                            action='ASSIGNED',
                            to_status=task.status,
                            details=f'Affectée à {task.assigned_to.get_full_name() or task.assigned_to.email}',
                        )
                        messages.success(request, f'Tâche de nettoyage affectée — Chambre {room.number}.')
                        return redirect('housekeeping:list')

        # ── Démarrer ou terminer une tâche ────────────────────────────────────
        elif action in ('start', 'complete'):
            task_qs = HousekeepingTask.objects.select_for_update().select_related('room')
            if user.role == UserRole.HOUSEKEEPER:
                task_qs = task_qs.filter(assigned_to=user)
            with transaction.atomic():
                task = get_object_or_404(task_qs, pk=request.POST.get('task_id'))
                expected = TaskStatus.PENDING if action == 'start' else TaskStatus.IN_PROGRESS
                new_status = TaskStatus.IN_PROGRESS if action == 'start' else TaskStatus.COMPLETED

                if task.status != expected:
                    messages.error(request, 'Cette tâche a déjà changé d\u2019état. Actualisez la page.')
                elif task.room_id is None:
                    messages.error(request, 'La tâche doit être associée à une chambre avant d\u2019être traitée.')
                else:
                    room = Room.objects.select_for_update().get(pk=task.room_id)
                    old_status = task.status
                    task.status = new_status
                    task.updated_at = timezone.now()
                    update_fields = ['status', 'updated_at']
                    if new_status == TaskStatus.COMPLETED:
                        task.completed_at = timezone.now()
                        update_fields.append('completed_at')
                        # Chambre → AVAILABLE une fois le nettoyage validé
                        room.status = RoomStatus.AVAILABLE
                        room.save(update_fields=['status'])
                    task.save(update_fields=update_fields)
                    HousekeepingTaskHistory.objects.create(
                        task=task,
                        actor=user,
                        action='STATUS_CHANGED',
                        from_status=old_status,
                        to_status=new_status,
                    )
                    if new_status == TaskStatus.COMPLETED:
                        messages.success(request, f'Chambre {room.number} nettoyée et remise Disponible ✅')
                    else:
                        messages.success(request, f'Nettoyage de la chambre {room.number} démarré.')
                    return redirect('housekeeping:list')

        # ── Réaffecter une tâche existante ────────────────────────────────────
        elif action == 'reassign':
            if not can_assign:
                raise PermissionDenied('Action non autorisée.')
            with transaction.atomic():
                task = get_object_or_404(HousekeepingTask, pk=request.POST.get('task_id'))
                new_agent_pk = request.POST.get('new_agent')
                if new_agent_pk:
                    from accounts.models import User
                    new_agent = get_object_or_404(User, pk=new_agent_pk, role=UserRole.HOUSEKEEPER)
                    old_agent = task.assigned_to
                    task.assigned_to = new_agent
                    task.save(update_fields=['assigned_to'])
                    HousekeepingTaskHistory.objects.create(
                        task=task,
                        actor=user,
                        action='REASSIGNED',
                        details=f'Réaffectée de {old_agent} à {new_agent.get_full_name() or new_agent.email}',
                    )
                    messages.success(request, 'Tâche réaffectée avec succès.')
                    return redirect('housekeeping:list')
        else:
            raise PermissionDenied('Action Housekeeping non autorisée.')

    tasks = _visible_tasks(user)
    pending = tasks.filter(status=TaskStatus.PENDING)
    in_progress = tasks.filter(status=TaskStatus.IN_PROGRESS)
    completed_today = tasks.filter(
        status=TaskStatus.COMPLETED,
        completed_at__date=timezone.localdate(),
    )

    # Chambres à nettoyer sans tâche active
    rooms_without_task = Room.objects.filter(
        status=RoomStatus.TO_CLEAN
    ).exclude(
        housekeeping_tasks__status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
    )

    # Agents disponibles pour réaffectation
    from accounts.models import User as UserModel
    housekeepers = UserModel.objects.filter(role=UserRole.HOUSEKEEPER, is_active=True).order_by('last_name')

    return render(request, 'housekeeping/list.html', {
        'tasks': tasks,
        'pending': pending,
        'in_progress': in_progress,
        'completed_today': completed_today,
        'form': form,
        'can_assign': can_assign,
        'rooms_without_task': rooms_without_task,
        'housekeepers': housekeepers,
        'pending_count': pending.count(),
        'in_progress_count': in_progress.count(),
        'completed_today_count': completed_today.count(),
    })


@role_required(['ADMIN', 'DIRECTOR', 'HOUSEKEEPING_MGR', 'HOUSEKEEPER'])
def task_history(request, task_id):
    """Historique complet d'une tâche."""
    task = get_object_or_404(
        HousekeepingTask.objects.select_related('room', 'assigned_to', 'created_by')
                                .prefetch_related('history__actor'),
        pk=task_id,
    )
    user = request.user
    # La femme de chambre ne peut voir que ses propres tâches
    if user.role == UserRole.HOUSEKEEPER and task.assigned_to != user:
        raise PermissionDenied()
    return render(request, 'housekeeping/task_history.html', {'task': task})
