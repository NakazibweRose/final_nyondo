"""
URL configuration for stock project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from stockapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.stock_list, name='stock_list'),
    path('create_receipt/', views.create_receipt, name='create_receipt'),
    path('receipt/<int:receipt_id>/', views.goods_received_note, name='goods_received_note'),
    path('stock_edit/<int:pk>/', views.stock_edit, name='stock_edit'),
    path('delete_receipt/<int:receipt_id>/', views.delete_receipt, name='delete_receipt'),
    path('stock_report/', views.stock_report, name='stock_report'),
    path('sales/', include('salesapp.urls')),
]
