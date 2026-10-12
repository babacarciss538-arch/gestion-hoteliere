from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    path('movements/add/', views.stock_movement_create, name='stock_movement_create'),
]