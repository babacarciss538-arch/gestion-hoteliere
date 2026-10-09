from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserActivity

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'phone', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations Personnelles', {'fields': ('first_name', 'last_name', 'phone', 'avatar')}),
        ('Rôles et Permissions', {'fields': ('role', 'department', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('email',)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('user__email', 'action', 'ip_address')
