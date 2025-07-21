from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('booking/confirmation/<int:pk>/', views.booking_confirmation, name='booking_confirmation'),
] 