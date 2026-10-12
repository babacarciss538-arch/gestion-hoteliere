from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    path('', views.restaurant_index, name='index'),
    path('api/orders/', views.restaurant_orders_api, name='orders_api'),
]
