from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    path('', views.kitchen_kds, name='kds'),
]
