from django.contrib import admin
from .models import Category, Product, Booking

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
