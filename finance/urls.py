from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.finance_index, name='index'),
    path('invoices/new/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('expenses/new/', views.expense_create, name='expense_create'),
    path('taxes/new/', views.tax_create, name='tax_create'),
    path('refunds/new/', views.refund_create, name='refund_create'),
]