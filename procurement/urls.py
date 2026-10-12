from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('orders/', views.purchase_order_list, name='purchase_order_list'),
    path('orders/add/', views.purchase_order_create, name='purchase_order_create'),
    path('orders/<int:order_id>/receive/', views.receive_purchase_order, name='receive_purchase_order'),
    path('requests/', views.supply_request_list, name='supply_request_list'),
    path('requests/add/', views.create_supply_request, name='create_supply_request'),
]