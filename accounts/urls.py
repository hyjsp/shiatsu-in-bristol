from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('booking/<int:pk>/edit/', views.edit_booking, name='edit_booking'),
    path('booking/<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
] 