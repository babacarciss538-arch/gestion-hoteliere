from django.urls import path
from . import views

app_name = 'housekeeping'

urlpatterns = [
    path('', views.housekeeping_list, name='list'),
    path('task/<int:task_id>/history/', views.task_history, name='task_history'),
]
