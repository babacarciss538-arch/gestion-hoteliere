from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, UserActivity
from cashier.models import CashDiscrepancy, CashSession
from finance.models import Expense, Invoice, Payment, Refund, Tax
from housekeeping.models import HousekeepingTask, TaskStatus
from inventory.models import Product, StockAlertLevel
from inventory.models import ServiceRequest
from maintenance.models import MaintenanceTicket, TicketStatus
from reception.models import CheckIn
from reservations.models import Reservation, ReservationStatus
from restaurant.models import OrderStatus, RestaurantOrder
from procurement.models import Delivery, PurchaseOrder, PurchaseOrderStatus, Supplier
from rooms.models import Room, RoomStatus


def _common_metrics(user, today, days=1):
    total_rooms = Room.objects.count()
    occupied_rooms = Room.objects.filter(status=RoomStatus.OCCUPIED).count()
    start_date = today - timedelta(days=days - 1)
    date_range = {'created_at__date__range': (start_date, today)}
    today_payments = Payment.objects.filter(**date_range).aggregate(total=Sum('amount'))['total'] or 0
    expense_total = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    return {
        'today': today,
        'total_rooms': total_rooms,
        'available_rooms': Room.objects.filter(status=RoomStatus.AVAILABLE).count(),
        'occupied_rooms': occupied_rooms,
        'reserved_rooms': Room.objects.filter(status=RoomStatus.RESERVED).count(),
        'to_clean_rooms': Room.objects.filter(status=RoomStatus.TO_CLEAN).count(),
        'maintenance_rooms': Room.objects.filter(status=RoomStatus.MAINTENANCE).count(),
        'occupancy_rate': round(occupied_rooms / total_rooms * 100, 1) if total_rooms else 0,
        'today_checkins': CheckIn.objects.filter(actual_check_in__date__range=(start_date, today)).count(),
        'today_checkouts': CheckIn.objects.filter(expected_check_out__range=(start_date, today)).count(),
        'pending_reservations': Reservation.objects.filter(status=ReservationStatus.CONFIRMED, check_in_date__range=(start_date, today)).count(),
        'today_payments': today_payments,
        'payment_count': Payment.objects.filter(**date_range).count(),
        'invoice_count': Invoice.objects.count(),
        'invoice_total': Invoice.objects.aggregate(total=Sum('amount'))['total'] or 0,
        'expense_total': expense_total,
        'result_total': today_payments - expense_total,
        'tax_total': Tax.objects.aggregate(total=Sum('amount'))['total'] or 0,
        'refund_total': Refund.objects.aggregate(total=Sum('amount'))['total'] or 0,
        'supplier_count': Supplier.objects.filter(is_active=True).count(),
        'purchase_order_count': PurchaseOrder.objects.count(),
        'purchase_order_open': PurchaseOrder.objects.filter(status=PurchaseOrderStatus.ORDERED).count(),
        'delivery_pending': Delivery.objects.filter(is_received=False).count(),
        'month_payments': Payment.objects.filter(**date_range).aggregate(total=Sum('amount'))['total'] or 0,
        'restaurant_orders_today': RestaurantOrder.objects.filter(**date_range).count(),
        'restaurant_orders_open': RestaurantOrder.objects.filter(**date_range, status=OrderStatus.OPEN).count(),
        'restaurant_orders_paid': RestaurantOrder.objects.filter(**date_range, status=OrderStatus.PAID).count(),
        'restaurant_revenue_today': RestaurantOrder.objects.filter(**date_range, status=OrderStatus.PAID).aggregate(total=Sum('total_amount'))['total'] or 0,
        'critical_stock_count': Product.objects.filter(alert_level__in=[StockAlertLevel.CRITICAL, StockAlertLevel.OUT_OF_STOCK]).count(),
        'out_of_stock_count': Product.objects.filter(alert_level=StockAlertLevel.OUT_OF_STOCK).count(),
        'total_products': Product.objects.count(),
        'normal_stock_count': Product.objects.filter(alert_level=StockAlertLevel.NORMAL).count(),
        'committed_stock_total': Product.objects.aggregate(total=Sum('committed_quantity'))['total'] or 0,
        'service_request_open': ServiceRequest.objects.filter(is_fulfilled=False).count(),
        'housekeeping_pending': HousekeepingTask.objects.filter(status=TaskStatus.PENDING).count(),
        'housekeeping_in_progress': HousekeepingTask.objects.filter(status=TaskStatus.IN_PROGRESS).count(),
        'housekeeping_completed': HousekeepingTask.objects.filter(status=TaskStatus.COMPLETED).count(),
        'maintenance_open': MaintenanceTicket.objects.filter(status__in=[TicketStatus.OPEN, TicketStatus.ASSIGNED]).count(),
        'maintenance_assigned': MaintenanceTicket.objects.filter(status=TicketStatus.ASSIGNED).count(),
        'maintenance_completed': MaintenanceTicket.objects.filter(status=TicketStatus.CLOSED).count(),
        'active_cash_session': CashSession.objects.filter(cashier=user, is_closed=False).first(),
        'cash_discrepancy_count': CashDiscrepancy.objects.count(),
        'cash_discrepancy_total': CashDiscrepancy.objects.aggregate(
            expected=Sum('expected_amount'), actual=Sum('actual_amount'),
        ),
    }


def _admin_context(today):
    return {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'role_count': User.objects.values('role').distinct().count(),
        'activity_count': UserActivity.objects.count(),
        'recent_activities': UserActivity.objects.select_related('user').all()[:8],
        'system_alerts': Product.objects.filter(alert_level__in=[StockAlertLevel.CRITICAL, StockAlertLevel.OUT_OF_STOCK]).count() + MaintenanceTicket.objects.filter(status__in=[TicketStatus.OPEN, TicketStatus.ASSIGNED]).count() + ServiceRequest.objects.filter(is_fulfilled=False).count(),
        'today': today,
    }


@login_required
def dashboard_index(request):
    today = timezone.now().date()
    period = request.GET.get('period', 'today')
    period_label = {'7': '7 derniers jours', '30': '30 derniers jours'}.get(period, "Aujourd'hui")
    role = getattr(request.user, 'role', 'RECEPTIONIST')

    if request.user.is_superuser or role == 'ADMIN':
        return render(request, 'dashboards/admin.html', _admin_context(today))

    days = {'7': 7, '30': 30}.get(period, 1)
    context = _common_metrics(request.user, today, days)
    context['role'] = role
    context['period'] = period
    context['period_label'] = period_label
    dashboard_by_role = {
        'DIRECTOR': 'dashboards/director.html',
        'RECEPTIONIST': 'dashboards/reception.html',
        'BOOKING_AGENT': 'dashboards/reception.html',
        'HOUSEKEEPING_MGR': 'dashboards/housekeeping.html',
        'HOUSEKEEPER': 'dashboards/housekeeping.html',
        'MAINTENANCE_MGR': 'dashboards/maintenance.html',
        'TECHNICIAN': 'dashboards/maintenance.html',
        'STOREKEEPER': 'dashboards/storekeeper.html',
        'KITCHEN_MGR': 'dashboards/kitchen.html',
        'COOK': 'dashboards/kitchen.html',
        'RESTAURANT_MGR': 'dashboards/restaurant.html',
        'WAITER': 'dashboards/restaurant.html',
        'CASHIER': 'dashboards/cashier.html',
        'ACCOUNTANT': 'dashboards/finance.html',
        'NIGHT_AUDITOR': 'dashboards/finance.html',
    }
    return render(request, dashboard_by_role.get(role, 'dashboards/reception.html'), context)