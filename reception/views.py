from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from accounts.permissions import role_required
from reservations.models import Reservation, ReservationStatus
from rooms.models import Room, RoomStatus
from .models import CheckIn

@role_required(['DIRECTOR', 'RECEPTIONIST', 'NIGHT_AUDITOR'])
def reception_index(request):
    today = timezone.localdate()

    if request.method == 'POST' and request.POST.get('action') == 'check_in':
        reservation = get_object_or_404(
            Reservation.objects.select_related('room'),
            pk=request.POST.get('reservation_id'),
            status=ReservationStatus.CONFIRMED,
            check_in_date__lte=today,
            room__isnull=False,
        )
        if CheckIn.objects.filter(reservation=reservation).exists():
            messages.error(request, 'Cette réservation possède déjà un enregistrement d’arrivée.')
        elif reservation.room.status not in (RoomStatus.AVAILABLE, RoomStatus.RESERVED):
            messages.error(request, 'La chambre n’est pas disponible pour cette arrivée.')
        else:
            with transaction.atomic():
                room = Room.objects.select_for_update().get(pk=reservation.room_id)
                if room.status not in (RoomStatus.AVAILABLE, RoomStatus.RESERVED):
                    messages.error(request, 'La chambre n’est pas disponible pour cette arrivée.')
                else:
                    CheckIn.objects.create(
                        reservation=reservation,
                        actual_check_in=timezone.now(),
                        expected_check_out=reservation.check_out_date,
                    )
                    room.status = RoomStatus.OCCUPIED
                    room.save(update_fields=['status'])
                    messages.success(request, 'Arrivée enregistrée.')
                    return redirect('reception:index')
    elif request.method == 'POST' and request.POST.get('action') == 'check_out':
        check_in = get_object_or_404(
            CheckIn.objects.select_related('reservation__room'),
            pk=request.POST.get('check_in_id'),
            actual_check_out__isnull=True,
            reservation__isnull=False,
        )
        with transaction.atomic():
            check_in = CheckIn.objects.select_for_update().get(pk=check_in.pk)
            reservation = Reservation.objects.select_for_update().get(pk=check_in.reservation_id)
            room = Room.objects.select_for_update().get(pk=reservation.room_id)
            check_in.actual_check_out = timezone.now()
            check_in.save(update_fields=['actual_check_out'])
            reservation.status = ReservationStatus.COMPLETED
            reservation.save(update_fields=['status'])
            room.status = RoomStatus.TO_CLEAN
            room.save(update_fields=['status'])
        messages.success(request, 'Départ enregistré; la chambre passe au statut à nettoyer.')
        return redirect('reception:index')
    elif request.method == 'POST':
        messages.error(request, 'Action de réception inconnue.')

    arrivals = Reservation.objects.filter(
        status=ReservationStatus.CONFIRMED,
        check_in_date__lte=today,
        room__isnull=False,
    ).filter(
        Q(check_out_date__isnull=True) | Q(check_out_date__gte=today),
        check_in_record__isnull=True,
    ).select_related('guest', 'room').order_by('check_in_date')
    in_house = CheckIn.objects.filter(
        actual_check_in__isnull=False,
        actual_check_out__isnull=True,
        reservation__isnull=False,
    ).select_related('reservation__guest', 'reservation__room').order_by('expected_check_out')
    return render(request, 'reception/index.html', {
        'arrivals': arrivals,
        'in_house': in_house,
    })
