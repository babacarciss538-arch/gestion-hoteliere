from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('<int:pk>/edit/', views.reservation_edit, name='edit'),
    path('', views.reservation_list, name='list'),
]
