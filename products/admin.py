from django.contrib import admin
from .models import Category, Product, Booking
from django.db import IntegrityError
from django.contrib import messages

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration_minutes', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'session_date', 'session_time', 'created_at']
    list_filter = ['session_date', 'product']
    search_fields = ['user__email', 'product__name']

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except IntegrityError:
            self.message_user(request, "A booking already exists for this date and time. Please choose another slot.", level=messages.ERROR)
