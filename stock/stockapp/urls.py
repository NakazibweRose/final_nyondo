from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('create/', views.create_receipt, name='create_receipt'),
    path('edit/<int:pk>/', views.stock_edit, name='stock_edit'),
    path('delete/<int:pk>/', views.delete_receipt, name='delete_receipt'),
    path('report/', views.stock_report, name='stock_report'),
    path('supplier-report/', views.supplier_report, name='supplier_report'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('goods-received-note/<int:receipt_id>/', views.goods_received_note, name='goods_received_note'),
    
]