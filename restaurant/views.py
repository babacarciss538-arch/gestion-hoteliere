from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import UserRole
from accounts.permissions import role_required
from cashier.models import CashSession
from finance.models import Payment, PaymentSource
from reception.models import CheckIn

from .forms import MenuItemForm, RestaurantOrderCreateForm
from .models import MenuCategory, MenuItem, OrderItem, OrderStatus, PaymentType, RestaurantOrder


STAFF_ROLES = ['ADMIN', 'DIRECTOR', 'RESTAURANT_MGR', 'WAITER', 'KITCHEN_MGR', 'COOK', 'CASHIER']
MANAGER_ROLES = ['ADMIN', 'DIRECTOR', 'RESTAURANT_MGR']


@role_required(STAFF_ROLES)
def restaurant_index(request):
    """Tableau de bord Restaurant POS, prise de commande, cuisine et caisse."""
    user = request.user
    is_manager = user.is_superuser or user.role in MANAGER_ROLES
    is_server = user.role == UserRole.WAITER
    is_kitchen = user.role in (UserRole.KITCHEN_MGR, UserRole.COOK)

    # 1. Prise de commande par le serveur
    if request.method == 'POST' and request.POST.get('action') == 'create_order':
        order_form = RestaurantOrderCreateForm(request.POST)
        if order_form.is_valid():
            with transaction.atomic():
                order = order_form.save(commit=False)
                order.server = user
                order.status = OrderStatus.RECEIVED
                order.save()

                # Traitement des lignes d'articles commandés
                items_data = request.POST.getlist('menu_items[]')
                quantities = request.POST.getlist('quantities[]')

                total = Decimal('0.00')
                for item_id, qty in zip(items_data, quantities):
                    try:
                        quantity = int(qty)
                        if quantity > 0:
                            menu_item = MenuItem.objects.get(pk=item_id)
                            OrderItem.objects.create(
                                order=order,
                                item=menu_item,
                                quantity=quantity,
                                unit_price=menu_item.price,
                            )
                            total += (menu_item.price * Decimal(quantity))
                    except (ValueError, MenuItem.DoesNotExist):
                        continue

                order.total_amount = total
                order.description = f"Commande {order.items.count()} article(s)"
                order.save(update_fields=['total_amount', 'description'])

                messages.success(request, f"Commande #{order.id} enregistrée et transmise ({total} FCFA).")
                return redirect('restaurant:index')
        else:
            messages.error(request, "Veuillez vérifier les informations saisies.")
    else:
        order_form = RestaurantOrderCreateForm()

    # 2. Transition des statuts (Cuisine / Service)
    if request.method == 'POST' and request.POST.get('action') == 'update_status':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_status')
        order = get_object_or_404(RestaurantOrder, pk=order_id)

        valid_transitions = [
            OrderStatus.RECEIVED, OrderStatus.PREPARING,
            OrderStatus.READY, OrderStatus.SERVED,
        ]
        if new_status in valid_transitions:
            order.status = new_status
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f"Commande #{order.id} passée à « {order.get_status_display()} ».")
            return redirect('restaurant:index')

    # 3. Règlement direct en caisse ou Imputation sur chambre
    if request.method == 'POST' and request.POST.get('action') == 'settle_order':
        order_id = request.POST.get('order_id')
        settlement_mode = request.POST.get('settlement_mode')
        order = get_object_or_404(RestaurantOrder, pk=order_id)

        if order.is_settled:
            messages.error(request, "Cette commande est déjà soldée ou imputée.")
            return redirect('restaurant:index')

        with transaction.atomic():
            if settlement_mode == 'ROOM':
                check_in_id = request.POST.get('check_in_id') or order.check_in_id
                check_in = get_object_or_404(CheckIn, pk=check_in_id)
                if check_in.actual_check_out is not None:
                    messages.error(request, "Le client a déjà effectué son Check-Out.")
                    return redirect('restaurant:index')

                order.check_in = check_in
                order.payment_type = PaymentType.ROOM
                order.status = OrderStatus.CHARGED_TO_ROOM
                order.save(update_fields=['check_in', 'payment_type', 'status', 'updated_at'])
                messages.success(request, f"Commande #{order.id} imputée sur la Chambre {check_in.room_number}.")

            elif settlement_mode == 'DIRECT':
                payment_method = request.POST.get('payment_method', 'CASH')
                cash_session = CashSession.objects.filter(is_closed=False).first()

                payment = Payment.objects.create(
                    amount=order.total_amount,
                    source=PaymentSource.RESTAURANT,
                    payment_method=payment_method,
                    cash_session=cash_session,
                    created_by=user,
                )
                order.payment = payment
                order.payment_type = PaymentType.DIRECT
                order.status = OrderStatus.PAID
                order.save(update_fields=['payment', 'payment_type', 'status', 'updated_at'])
                messages.success(request, f"Commande #{order.id} encaissée (Source: Restaurant).")

            return redirect('restaurant:index')

    orders_qs = RestaurantOrder.objects.select_related(
        'server', 'check_in__reservation__room', 'check_in__reservation__guest', 'payment'
    ).prefetch_related('items__item')

    status_filter = request.GET.get('status', '')
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    categories = MenuCategory.objects.prefetch_related('items').all()
    active_stays = CheckIn.objects.filter(
        actual_check_in__isnull=False,
        actual_check_out__isnull=True,
        reservation__isnull=False,
    ).select_related('reservation__guest', 'reservation__room')

    today = timezone.localdate()
    today_orders = RestaurantOrder.objects.filter(created_at__date=today)
    revenue_paid = sum((o.total_amount for o in today_orders.filter(status=OrderStatus.PAID)), Decimal('0.00'))
    revenue_room = sum((o.total_amount for o in today_orders.filter(status=OrderStatus.CHARGED_TO_ROOM)), Decimal('0.00'))

    context = {
        'order_form': order_form,
        'orders': orders_qs[:80],
        'categories': categories,
        'active_stays': active_stays,
        'is_manager': is_manager,
        'is_server': is_server,
        'is_kitchen': is_kitchen,
        'status_choices': OrderStatus.choices,
        'status_filter': status_filter,
        'revenue_paid': revenue_paid,
        'revenue_room': revenue_room,
        'pending_count': today_orders.filter(status__in=[OrderStatus.RECEIVED, OrderStatus.PREPARING]).count(),
    }
    return render(request, 'restaurant/index.html', context)


@role_required(STAFF_ROLES)
def restaurant_orders_api(request):
    """API JSON temps réel pour actualisation KDS et Caisse."""
    orders = RestaurantOrder.objects.filter(
        status__in=[OrderStatus.RECEIVED, OrderStatus.PREPARING, OrderStatus.READY]
    ).select_related('server', 'check_in__reservation__room').order_by('created_at')

    data = []
    for o in orders:
        data.append({
            'id': o.id,
            'table': o.table_number or (f"Chambre {o.check_in.room_number}" if o.check_in else "Emporter"),
            'status': o.status,
            'status_display': o.get_status_display(),
            'total': str(o.total_amount),
            'notes': o.notes,
            'items': [f"{it.quantity}x {it.item.name}" for it in o.items.all()],
            'created_at': o.created_at.strftime('%H:%M'),
        })
    return JsonResponse({'orders': data})
