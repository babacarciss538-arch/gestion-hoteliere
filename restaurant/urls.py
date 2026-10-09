from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    path('', views.restaurant_index, name='index'),
]
