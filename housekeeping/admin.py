from django.contrib import admin
from .models import HousekeepingTask, HousekeepingTaskHistory


class HousekeepingTaskHistoryInline(admin.TabularInline):
    model = HousekeepingTaskHistory
    extra = 0
    readonly_fields = ('actor', 'action', 'from_status', 'to_status', 'details', 'created_at')
    can_delete = False


@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'room', 'assigned_to', 'priority', 'status', 'created_at', 'completed_at')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'room__number', 'assigned_to__email')
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    inlines = [HousekeepingTaskHistoryInline]


@admin.register(HousekeepingTaskHistory)
class HousekeepingTaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task', 'actor', 'action', 'from_status', 'to_status', 'created_at')
    list_filter = ('action',)
    readonly_fields = ('created_at',)
