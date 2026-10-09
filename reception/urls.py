from django.urls import path
from . import views

app_name = 'reception'

urlpatterns = [
    path('', views.reception_index, name='index'),
]
