from django.urls import path
from . import views

app_name = 'commercial'

urlpatterns = [
    path('', views.commercial_index, name='index'),
]
