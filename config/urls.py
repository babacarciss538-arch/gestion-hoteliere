from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls', namespace='dashboard')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('rooms/', include('rooms.urls', namespace='rooms')),
    path('guests/', include('guests.urls', namespace='guests')),
    path('reservations/', include('reservations.urls', namespace='reservations')),
    path('reception/', include('reception.urls', namespace='reception')),
    path('housekeeping/', include('housekeeping.urls', namespace='housekeeping')),
    path('maintenance/', include('maintenance.urls', namespace='maintenance')),
    path('restaurant/', include('restaurant.urls', namespace='restaurant')),
    path('kitchen/', include('kitchen.urls', namespace='kitchen')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('procurement/', include('procurement.urls', namespace='procurement')),
    path('cashier/', include('cashier.urls', namespace='cashier')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('hr/', include('hr.urls', namespace='hr')),
    path('commercial/', include('commercial.urls', namespace='commercial')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('audit/', include('audit.urls', namespace='audit')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
