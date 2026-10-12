from django.contrib import admin
from .models import MaintenanceTicket, MaintenanceTicketHistory


class MaintenanceTicketHistoryInline(admin.TabularInline):
    model = MaintenanceTicketHistory
    extra = 0
    readonly_fields = ('actor', 'action', 'from_status', 'to_status', 'details', 'created_at')
    can_delete = False


@admin.register(MaintenanceTicket)
class MaintenanceTicketAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'room', 'location', 'priority', 'status',
        'technician_type', 'assigned_technician', 'external_company',
        'reported_by', 'created_at',
    )
    list_filter = ('status', 'priority', 'technician_type')
    search_fields = ('title', 'description', 'location', 'room__number', 'external_company')
    readonly_fields = ('created_at', 'updated_at', 'assigned_at', 'resolved_at', 'closed_at')
    inlines = [MaintenanceTicketHistoryInline]


@admin.register(MaintenanceTicketHistory)
class MaintenanceTicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'actor', 'action', 'from_status', 'to_status', 'created_at')
    list_filter = ('action',)
    readonly_fields = ('created_at',)
