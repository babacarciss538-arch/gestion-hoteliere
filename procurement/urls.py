from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('', views.procurement_list, name='list'),
]
