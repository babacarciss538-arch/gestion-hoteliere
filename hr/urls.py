from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.hr_index, name='index'),
]
